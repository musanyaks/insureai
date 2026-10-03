"""Report assembly: structured fields from typed payloads, evidence lines derived
from claim-context facts only, narrative from template (LLM enhancement optional
and strictly grounded — it receives the report JSON and is forbidden to invent
numbers). JSONB writes go through model_dump_json round-trips so dates/decimals
serialize safely."""
from __future__ import annotations

import logging
from datetime import date

from insureai.agents.orchestrator.routing import recommended_actions, route_after_fraud
from insureai.schemas.fraud import FraudResult
from insureai.schemas.report import AgentContribution, InvestigationReport

logger = logging.getLogger(__name__)

# Moves to llm/prompts/ with the RAG commit.
NARRATIVE_SYSTEM = (
    "You write 3-5 sentence fraud-desk investigation narratives for insurance "
    "claims. Use ONLY the facts and numbers in the provided JSON. Never invent "
    "evidence, names, or figures. Neutral, factual tone."
)


def _pd(x):
    if isinstance(x, date):
        return x
    if isinstance(x, str):
        try:
            return date.fromisoformat(x[:10])
        except ValueError:
            return None
    return None


def _evidence(ctx: dict) -> list[str]:
    ev: list[str] = []
    claim = ctx.get("claim", {})
    prior = ctx.get("prior_claims_12m") or {}
    if int(prior.get("count") or 0) > 0:
        ev.append(f"{int(prior['count'])} prior claim(s) on this policy in the trailing "
                  f"12 months (KES {float(prior.get('total_amount') or 0):,.0f})")
    inc, loss = _pd(claim.get("inception_date")), _pd(claim.get("loss_date"))
    if inc and loss and 0 <= (loss - inc).days <= 60:
        ev.append(f"Loss occurred {(loss - inc).days} day(s) after policy inception")
    repair, book = claim.get("repair_estimate"), claim.get("book_value_cost")
    if repair and book and float(book) > 0:
        ev.append(f"Repair estimate is {float(repair) / float(book):.2f}x independent book cost")
    for e in ctx.get("entity_links", []):
        others, fraud_o = int(e.get("other_links") or 0), int(e.get("other_fraud_links") or 0)
        if others or fraud_o:
            line = f"{e['entity_type']} identifier shared with {others} other-policy claim(s)"
            if fraud_o:
                line += f", {fraud_o} previously flagged as fraud"
            ev.append(line)
    if (claim.get("accident_county") and claim.get("policy_county")
            and claim["accident_county"] != claim["policy_county"]):
        ev.append(f"Accident county ({claim['accident_county']}) differs from policy "
                  f"county ({claim['policy_county']})")
    if claim.get("nights_weekend"):
        ev.append("Loss occurred during the night/weekend window")
    if claim.get("theft_flag"):
        ev.append("Reported as theft")
    return ev


def _template_narrative(report: InvestigationReport) -> str:
    top = "; ".join(report.evidence[:3]) or "no adverse indicators"
    nxt = report.recommended_actions[0] if report.recommended_actions else "standard processing"
    return (f"Claim {report.claim_id} scored {report.fraud_probability:.0%} fraud "
            f"probability ({report.risk_level.value}). Key evidence: {top}. "
            f"Recommended next step: {nxt}.")


def _llm():
    try:
        from insureai.llm.client import LLMClient
        client = LLMClient()
        return client if client.available else None
    except Exception:
        return None


def build_report(investigation_id: str, ctx: dict, result: FraudResult) -> InvestigationReport:
    report = InvestigationReport(
        investigation_id=investigation_id,
        claim_id=result.claim_id or str(ctx.get("claim", {}).get("claim_id", "")),
        fraud_probability=result.fraud_probability,
        risk_level=result.risk_level,
        evidence=_evidence(ctx),
        agents_consulted=[
            AgentContribution(
                agent="claims",
                summary="Claim context assembled: policy, 12-month history, entity links",
                data={"prior_claims_12m": ctx.get("prior_claims_12m", {}),
                      "entity_link_count": len(ctx.get("entity_links", []))},
            ),
            AgentContribution(
                agent="fraud",
                summary=(f"Scored {result.fraud_probability:.0%} "
                         f"({result.risk_level.value}) by {result.model_version}"),
                data={"reason_codes": [rc.model_dump() for rc in result.reason_codes]},
            ),
        ],
        recommended_actions=recommended_actions(route_after_fraud(result.fraud_probability)),
        confidence=round(min(0.8, 0.55 + 0.05 * len(result.reason_codes)), 2),
    )
    report.narrative = _template_narrative(report)
    llm = _llm()
    if llm is not None:
        try:
            report.narrative = llm.complete(NARRATIVE_SYSTEM, report.model_dump_json())
        except Exception:
            logger.warning("LLM narrative failed — keeping template", exc_info=True)
    return report