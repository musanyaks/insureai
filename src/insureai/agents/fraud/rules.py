"""Deterministic heuristic scorer — the v1 fraud model behind the gate (ADR-006).
Transparent additive weights, calibrated to known typologies; replaced by
XGBoost+SHAP behind the identical FraudResult contract. Every reason description
is derived from a fact in the context — nothing is invented, which is what the
report-faithfulness eval will later assert."""
from __future__ import annotations

from datetime import date, datetime

EARLY_WINDOW_DAYS = 30
INFLATION_RATIO_HIGH = 1.40
INFLATION_RATIO_MILD = 1.20
HIGH_SEVERITY_RATIO = 0.60
AGED_VEHICLE_YEARS = 12
MAX_SCORE = 0.95


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _d(x):
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    if isinstance(x, str):
        try:
            return date.fromisoformat(x[:10])
        except ValueError:
            return None
    return None


def score_claim(ctx: dict) -> tuple[float, list[dict]]:
    """Returns (probability, reason-code dicts). Pure function of the context."""
    claim = ctx.get("claim", {})
    reasons: list[dict] = []
    score = 0.0

    def add(code: str, description: str, weight: float) -> None:
        nonlocal score
        score += weight
        reasons.append({"code": code, "description": description, "contribution": weight})

    # -- Timing: early-claim window (EARLY_CLAIM typology)
    inception, loss = _d(claim.get("inception_date")), _d(claim.get("loss_date"))
    if inception and loss and 0 <= (loss - inception).days <= EARLY_WINDOW_DAYS:
        days = (loss - inception).days
        add("EARLY_CLAIM_WINDOW", f"Loss occurred {days} day(s) after policy inception", 0.50)

    # -- Cost ratios (INFLATION typology)
    repair, book = _f(claim.get("repair_estimate")), _f(claim.get("book_value_cost"))
    if book > 0 and repair > 0:
        ratio = repair / book
        if ratio >= INFLATION_RATIO_HIGH:
            add("REPAIR_ESTIMATE_INFLATED",
                f"Repair estimate is {ratio:.2f}x independent book cost", 0.35)
        elif ratio >= INFLATION_RATIO_MILD:
            add("REPAIR_ESTIMATE_ELEVATED",
                f"Repair estimate is {ratio:.2f}x independent book cost", 0.12)

    # -- Shared entities (RING typology) — links already exclude same-policy claims
    phone_shared = bank_shared = garage_dense = fraud_linked = False
    for e in ctx.get("entity_links", []):
        etype = e.get("entity_type")
        others, fraud_others = int(_f(e.get("other_links"))), int(_f(e.get("other_fraud_links")))
        if etype == "PHONE" and others >= 1:
            phone_shared = True
        if etype == "BANK" and others >= 1:
            bank_shared = True
        if etype == "GARAGE" and others >= 3:
            garage_dense = True
        if fraud_others >= 1:
            fraud_linked = True
    if phone_shared or bank_shared:
        add("SHARED_CONTACT_ENTITY",
            "Phone/bank identifier shared with claims on other policies", 0.30)
    if phone_shared and bank_shared:
        add("RING_SIGNATURE", "Multiple identifier types shared across policies", 0.15)
    if garage_dense:
        add("GARAGE_CLAIM_DENSITY", "Garage appears on 3+ claims from other policies", 0.15)
    if fraud_linked:
        add("FRAUD_LINKED_ENTITY",
            "Shared identifier appears on previously flagged fraudulent claims", 0.20)

    # -- Geography & behaviour (GEO_ANOMALY typology)
    if (claim.get("accident_county") and claim.get("policy_county")
            and claim["accident_county"] != claim["policy_county"]
            and claim.get("nights_weekend")):
        add("GEO_NIGHT_ANOMALY",
            f"Loss in {claim['accident_county']} differs from policy county "
            f"({claim['policy_county']}) during night/weekend", 0.20)
    year = int(_f(claim.get("vehicle_year")))
    if claim.get("theft_flag") and year and (2026 - year) >= AGED_VEHICLE_YEARS:
        add("THEFT_AGED_VEHICLE", f"Theft of a {2026 - year}-year-old vehicle", 0.15)

    # -- Exposure & history
    value, amount = _f(claim.get("vehicle_value")), _f(claim.get("claim_amount"))
    if value > 0 and amount / value >= HIGH_SEVERITY_RATIO:
        add("HIGH_SEVERITY_RATIO", f"Claim is {amount / value:.0%} of vehicle value", 0.12)
    prior = ctx.get("prior_claims_12m") or {}
    if int(_f(prior.get("count"))) >= 2:
        add("REPEAT_CLAIMS",
            f"{int(_f(prior.get('count')))} prior claims on this policy in 12 months", 0.15)

    return min(round(score, 3), MAX_SCORE), reasons