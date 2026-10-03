"""The final report is assembled from structured agent outputs. The LLM writes
only the `narrative` field — every other field came from typed payloads."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from insureai.schemas.fraud import FraudRiskLevel


class AgentContribution(BaseModel):
    agent: str
    summary: str
    data: dict[str, Any]


class InvestigationReport(BaseModel):
    investigation_id: str
    claim_id: str
    fraud_probability: float
    risk_level: FraudRiskLevel
    evidence: list[str]
    agents_consulted: list[AgentContribution]
    recommended_actions: list[str]
    confidence: float
    narrative: str = ""          # LLM-authored; numbers above are not
    human_decision: str | None = None   # set when the HITL gate resolves
    audit_id: str = ""