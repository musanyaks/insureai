"""FraudResult is the boundary between scoring and narrative. Score and reason
codes come from the scorer (heuristics now, XGBoost+SHAP later) — numbers never
pass through an LLM (ADR-003)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

HIGH_THRESHOLD = 0.70
MEDIUM_THRESHOLD = 0.40


class FraudRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


def risk_level_for(probability: float) -> FraudRiskLevel:
    if probability >= HIGH_THRESHOLD:
        return FraudRiskLevel.HIGH
    if probability >= MEDIUM_THRESHOLD:
        return FraudRiskLevel.MEDIUM
    return FraudRiskLevel.LOW


class ReasonCode(BaseModel):
    code: str                 # e.g. "REPAIR_ESTIMATE_INFLATED"
    description: str          # human-readable, template-derived from facts
    contribution: float       # signed contribution to the score (SHAP-derived once ML lands)


class FraudResult(BaseModel):
    claim_id: str
    fraud_probability: float = Field(ge=0.0, le=1.0)
    risk_level: FraudRiskLevel
    reason_codes: list[ReasonCode]
    model_version: str
    scored_at: datetime