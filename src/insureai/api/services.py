"""Investigation lifecycle helpers, shared by API routes and the orchestrator.
Auditing happens at the consumption point (BaseAgent records every envelope it
processes) — the API publishes, agents audit."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from insureai.schemas.envelope import AgentEnvelope, Priority

HIGH_VALUE_THRESHOLD = 1_000_000  # KES — deterministic priority rule
ACTIVE_STATUSES = ("RUNNING", "AWAITING_APPROVAL")


def ensure_investigation(conn, *, claim_id: str) -> dict[str, Any] | None:
    """Idempotent create-or-get of the active investigation for a claim.
    Returns None if the claim doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("SELECT claim_id, claim_amount FROM claims WHERE claim_id = %s",
                    (claim_id,))
        claim = cur.fetchone()
        if claim is None:
            return None
        cur.execute(
            "SELECT investigation_id, status FROM investigations "
            "WHERE claim_id = %s AND status = ANY(%s) LIMIT 1",
            (claim_id, list(ACTIVE_STATUSES)),
        )
        existing = cur.fetchone()
        if existing:
            return {"claim_id": claim_id, "claim_amount": float(claim["claim_amount"]),
                    "investigation_id": existing["investigation_id"],
                    "status": existing["status"], "already_running": True}
        inv_id = f"INV-{uuid4().hex[:12].upper()}"
        cur.execute("INSERT INTO investigations (investigation_id, claim_id) VALUES (%s, %s)",
                    (inv_id, claim_id))
        return {"claim_id": claim_id, "claim_amount": float(claim["claim_amount"]),
                "investigation_id": inv_id, "status": "RUNNING", "already_running": False}


def start_investigation(pool, bus, audit, *, claim_id: str, trigger: str,
                        requested_by: str | None) -> dict[str, Any] | None:
    """API entry: ensure the investigation, publish claim.review_requested.
    (audit param retained for call-site compatibility; recording is the
    consumer's job now.)"""
    with pool.connection() as conn:
        inv = ensure_investigation(conn, claim_id=claim_id)
    if inv is None:
        return None
    if inv["already_running"]:
        return {"investigation_id": inv["investigation_id"], "claim_id": claim_id,
                "status": inv["status"], "priority": None, "already_running": True}
    priority = (Priority.HIGH if inv["claim_amount"] >= HIGH_VALUE_THRESHOLD
                else Priority.MEDIUM)
    bus.publish(AgentEnvelope(
        correlation_id=inv["investigation_id"],
        from_agent="api", to_agent="orchestrator",
        event="claim.review_requested", priority=priority,
        payload={"claim_id": claim_id, "trigger": trigger,
                 "requested_by": requested_by, "claim_amount": inv["claim_amount"]},
    ))
    return {"investigation_id": inv["investigation_id"], "claim_id": claim_id,
            "status": "RUNNING", "priority": priority.value, "already_running": False}