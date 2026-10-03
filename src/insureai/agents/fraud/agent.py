"""Fraud Detection Agent. v1: heuristic rules. ML swap (XGBoost+SHAP) replaces
score_claim() only — this file, the envelope contract, routing, HITL and
reporting are untouched. No DB access by design: pure function of the context."""
from __future__ import annotations

from datetime import datetime, timezone

from insureai.agents.base import BaseAgent
from insureai.agents.fraud.rules import score_claim
from insureai.schemas.fraud import FraudResult, ReasonCode, risk_level_for


class FraudAgent(BaseAgent):
    name = "fraud"
    MODEL_VERSION = "heuristic-rules-v1"

    def handle(self, envelope):
        if envelope.event != "fraud.score_requested":
            return None
        ctx = envelope.payload
        probability, reasons = score_claim(ctx)
        result = FraudResult(
            claim_id=str(ctx.get("claim", {}).get("claim_id", "")),
            fraud_probability=probability,
            risk_level=risk_level_for(probability),
            reason_codes=[ReasonCode(**r) for r in reasons],
            model_version=self.MODEL_VERSION,
            scored_at=datetime.now(timezone.utc),
        )
        return envelope.reply("fraud.score_completed", {"result": result.model_dump()})