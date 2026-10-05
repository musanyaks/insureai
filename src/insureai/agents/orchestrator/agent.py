"""AI Orchestrator: a stateless, event-driven finite state machine (ADR-005).
Durable state = investigations.status + report + the agent_messages audit trail
(the claim.context envelope IS the pipeline's working memory). Every outbound
envelope is routed by deterministic gates; the orchestrator never computes a
number itself."""
from __future__ import annotations

import json
import logging

from psycopg.types.json import Jsonb

from insureai.agents.base import BaseAgent
from insureai.agents.orchestrator.report import build_report
from insureai.agents.orchestrator.routing import recommended_actions, route_after_fraud
from insureai.db import clean_row, get_conn
from insureai.api.services import ensure_investigation
from insureai.schemas.envelope import AgentEnvelope, Priority
from insureai.schemas.fraud import FraudResult
from insureai.schemas.report import InvestigationReport

logger = logging.getLogger(__name__)

BROADCAST_SINK = "api"   # envelopes published for observability; no handler


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"
    AUTO_INVESTIGATE_THRESHOLD = 1_000_000  # KES — auto-investigate high-value intake

    def __init__(self, bus, audit=None, dsn: str | None = None) -> None:
        super().__init__(bus, audit)
        self.dsn = dsn

    # -- dispatch -----------------------------------------------------------
    def handle(self, envelope):
        ev = envelope.event
        if ev == "claim.review_requested":
            self._start_pipeline(envelope, str(envelope.payload.get("claim_id", "")))
        elif ev == "claim.registered":
            self._maybe_auto_investigate(envelope)
        elif ev == "claim.context":
            self._request_score(envelope)
        elif ev == "fraud.score_completed":
            self._on_score(envelope)
        elif ev == "approval.decided":
            self._on_decision(envelope)
        return None   # orchestrator publishes commands; nothing replies to it

    # -- pipeline steps -----------------------------------------------------
        def _start_pipeline(self, env: AgentEnvelope, claim_id: str) -> None:
        if not claim_id:
            return
        with get_conn(self.dsn) as conn:
            inv = ensure_investigation(conn, claim_id=claim_id)
        if inv is None:
            return
        inv_id = inv["investigation_id"]
        # Replay-safety: an investigation created before the worker existed sits
        # in RUNNING with no pipeline activity — start it rather than bounce.
        if inv["already_running"] and self._pipeline_started(inv_id):
            return
        self.bus.publish(
            AgentEnvelope(
                correlation_id=inv_id, from_agent=self.name,
                to_agent="claims", event="claim.context_requested",
                priority=env.priority, payload={"claim_id": claim_id},
            ),
            topic=_commands_topic(self.bus),
        )

    def _pipeline_started(self, inv_id: str) -> bool:
        with get_conn(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM agent_messages WHERE correlation_id = %s "
                "AND event = 'claim.context_requested' LIMIT 1",
                (inv_id,),
            )
            return cur.fetchone() is not None)

    def _maybe_auto_investigate(self, env: AgentEnvelope) -> None:
        claim_id = str(env.payload.get("claim_id", ""))
        with get_conn(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT claim_amount FROM claims WHERE claim_id = %s", (claim_id,))
            row = cur.fetchone()
        if row and float(row["claim_amount"]) >= self.AUTO_INVESTIGATE_THRESHOLD:
            self._start_pipeline(env, claim_id)

    def _request_score(self, env: AgentEnvelope) -> None:
        """claim.context arrived -> forward the whole context to the fraud agent.
        The context is already durable in agent_messages (audit-at-consumption),
        so the orchestrator keeps no in-memory state."""
        self.bus.publish(
            AgentEnvelope(
                correlation_id=env.correlation_id, from_agent=self.name,
                to_agent="fraud", event="fraud.score_requested",
                priority=env.priority, payload=env.payload,
            ),
            topic=_commands_topic(self.bus),
        )

    def _on_score(self, env: AgentEnvelope) -> None:
        result = FraudResult.model_validate(env.payload["result"])
        inv_id = env.correlation_id
        ctx = self._latest_context(inv_id) or self._fallback_context(result.claim_id)
        route = route_after_fraud(result.fraud_probability)
        if route == "hitl":
            self._gate_for_approval(inv_id, result, ctx)
        else:
            self._complete(inv_id, result, ctx)

    # -- outcomes -----------------------------------------------------------
    def _gate_for_approval(self, inv_id: str, result: FraudResult, ctx: dict) -> None:
        report = build_report(inv_id, ctx, result)
        with get_conn(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO approvals (investigation_id, fraud_probability, recommendation) "
                "VALUES (%s, %s, %s) RETURNING approval_id",
                (inv_id, result.fraud_probability, "Refer for investigation"),
            )
            cur.fetchone()
            cur.execute(
                "UPDATE investigations SET status = 'AWAITING_APPROVAL', report = %s "
                "WHERE investigation_id = %s",
                (Jsonb(json.loads(report.model_dump_json())), inv_id),
            )
        self._broadcast(
            "investigation.awaiting_approval", inv_id,
            {"claim_id": result.claim_id, "fraud_probability": result.fraud_probability,
             "risk_level": result.risk_level.value, "approval_required": True},
            priority=Priority.HIGH,
        )

    def _on_decision(self, env: AgentEnvelope) -> None:
        inv_id = env.correlation_id
        decision = str(env.payload.get("decision", ""))
        with get_conn(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT claim_id, status, report FROM investigations "
                "WHERE investigation_id = %s", (inv_id,),
            )
            row = cur.fetchone()
            if row is None or row["status"] == "COMPLETED":   # idempotent
                return
            if row["report"]:
                report = InvestigationReport.model_validate(row["report"])
            else:   # legacy/missing report — build a minimal stub
                report = InvestigationReport(
                    investigation_id=inv_id, claim_id=row["claim_id"],
                    fraud_probability=float(env.payload.get("fraud_probability") or 0.0),
                    risk_level="HIGH", evidence=[], agents_consulted=[],
                    recommended_actions=[], confidence=0.0,
                )
            report.human_decision = decision
            if decision == "REJECTED":
                report.recommended_actions = [
                    "Claim rejected — no settlement. File retained for fraud records."]
            cur.execute(
                "UPDATE investigations SET status = 'COMPLETED', report = %s, "
                "completed_at = now() WHERE investigation_id = %s",
                (Jsonb(json.loads(report.model_dump_json())), inv_id),
            )
        self._broadcast(
            "investigation.completed", inv_id,
            {"claim_id": report.claim_id, "decision": decision},
            priority=Priority.HIGH,
        )

    def _complete(self, inv_id: str, result: FraudResult, ctx: dict) -> None:
        report = build_report(inv_id, ctx, result)
        with get_conn(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE investigations SET status = 'COMPLETED', report = %s, "
                "completed_at = now() WHERE investigation_id = %s AND status <> 'COMPLETED'",
                (Jsonb(json.loads(report.model_dump_json())), inv_id),
            )
        self._broadcast(
            "investigation.completed", inv_id,
            {"claim_id": result.claim_id,
             "fraud_probability": result.fraud_probability,
             "risk_level": result.risk_level.value},
        )

    # -- helpers ------------------------------------------------------------
    def _latest_context(self, correlation_id: str) -> dict | None:
        with get_conn(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT payload FROM agent_messages "
                "WHERE correlation_id = %s AND event = 'claim.context' "
                "ORDER BY id DESC LIMIT 1",
                (correlation_id,),
            )
            row = cur.fetchone()
        return row["payload"] if row else None

    def _fallback_context(self, claim_id: str) -> dict:
        """Only used if the audit row for claim.context is missing (e.g. audit
        outage mid-flight). Minimal context keeps the report honest."""
        with get_conn(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT c.*, p.county AS policy_county, p.vehicle_value, p.inception_date "
                "FROM claims c JOIN policies p USING (policy_id) WHERE c.claim_id = %s",
                (claim_id,),
            )
            row = cur.fetchone()
        return {"claim_id": claim_id, "claim": clean_row(row),
                "prior_claims_12m": {}, "entity_links": []}

    def _broadcast(self, event: str, inv_id: str, payload: dict,
                   priority: Priority = Priority.MEDIUM) -> None:
        env = AgentEnvelope(correlation_id=inv_id, from_agent=self.name,
                            to_agent=BROADCAST_SINK, event=event,
                            priority=priority, payload=payload)
        if self.audit:            # self-audit: broadcasts have no consumer to audit them
            self.audit.record(env)
        self.bus.publish(env, topic=_commands_topic(self.bus))


def _commands_topic(bus) -> str:
    from insureai.bus.topics import Topics
    return Topics.COMMANDS