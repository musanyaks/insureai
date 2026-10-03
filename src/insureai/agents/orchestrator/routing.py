"""Deterministic routing gates (ADR-003: business logic lives in code, not in
an LLM's judgment). The only decision an LLM ever makes in this platform is
phrasing; thresholds live in schemas/fraud.py as the single source."""
from __future__ import annotations

from insureai.schemas.fraud import HIGH_THRESHOLD, MEDIUM_THRESHOLD


def route_after_fraud(probability: float) -> str:
    if probability >= HIGH_THRESHOLD:
        return "hitl"
    if probability >= MEDIUM_THRESHOLD:
        return "enhanced"
    return "standard"


def recommended_actions(route: str) -> list[str]:
    if route == "hitl":
        return [
            "HUMAN DECISION REQUIRED — approve or reject in the approvals queue",
            "Assign to fraud investigation unit",
            "Preserve claim file and entity-link evidence",
        ]
    if route == "enhanced":
        return [
            "Request supporting documents (police abstract, repair invoices)",
            "Verify repair estimate against an independent assessor",
            "Claims officer review before settlement",
        ]
    return [
        "Standard processing — route to claims officer for settlement review",
    ]