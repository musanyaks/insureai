"""Fraud typology injection. Every injection mutates a clean claim in a way that
leaves real, derivable-at-score-time signals: timing, cost ratios, shared entities,
geography. Labels written here become the golden set and the model's training truth.

Typologies (weighted):
  INFLATION   0.35  - repair estimate 1.45-2.2x book cost
  EARLY_CLAIM 0.25  - loss 3-20 days after inception, same-day report
  RING        0.20  - shared phone/bank/garage across policies + linked history claim
  GEO_ANOMALY 0.20  - far county + night/weekend (+ theft for aged vehicles)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from data.synthetic.claims import Claim
from data.synthetic.policies import COUNTIES, SEVERITY_SIGMA, Policy

EARLY_DESCRIPTIONS = [
    "Single-vehicle accident, no third party involved",
    "Vehicle damaged in flooded estate, details unclear",
    "Accident reported by driver shortly after policy start",
]
RING_DESCRIPTIONS = [
    "Front-end damage, repairs directed to preferred garage",
    "Collision on highway, no police abstract available yet",
    "Multiple vehicle damage, third party not traceable",
]
GEO_DESCRIPTIONS = [
    "Theft of vehicle from unattended parking bay",
    "Night-time accident on rural road, no witnesses",
]
TYPOLOGIES = ["EARLY_CLAIM", "INFLATION", "RING", "GEO_ANOMALY"]
WEIGHTS = [0.25, 0.35, 0.20, 0.20]


@dataclass
class Ring:
    ring_id: str
    phone: str
    bank_account: str
    garage_id: str
    member_policy_ids: list[str] = field(default_factory=list)


def create_rings(policies: list[Policy], rng: np.random.Generator, n: int = 6) -> list[Ring]:
    rings = []
    for r in range(n):
        members = [p.policy_id for p in rng.choice(policies, size=int(rng.integers(3, 7)), replace=False)]
        rings.append(Ring(
            ring_id=f"RING-{r:02d}",
            phone=f"+2547{int(rng.integers(10_000_000, 99_999_999)):08d}",
            bank_account=f"{int(rng.integers(10_000_000, 99_999_999))}",
            garage_id=f"G-RING-{r:02d}",
            member_policy_ids=members,
        ))
    return rings


def inject_early_claim(rng: np.random.Generator, c: Claim, p: Policy) -> None:
    days_in = int(rng.integers(3, 21))
    c.loss_date = p.inception_date + timedelta(days=days_in)
    c.reported_date = c.loss_date + timedelta(days=int(rng.integers(0, 2)))
    c.claim_amount = round(min(p.vehicle_value * float(rng.uniform(0.45, 0.75)), p.sum_insured), 2)
    c.repair_estimate = round(c.claim_amount * float(rng.uniform(1.05, 1.25)), 2)
    c.loss_description = str(rng.choice(EARLY_DESCRIPTIONS))


def inject_inflation(rng: np.random.Generator, c: Claim, p: Policy) -> None:
    c.repair_estimate = round(c.claim_amount * float(rng.uniform(1.45, 2.2)), 2)
    c.book_value_cost = round(c.claim_amount * float(rng.uniform(0.85, 1.05)), 2)


def inject_geo_anomaly(rng: np.random.Generator, c: Claim, p: Policy) -> None:
    far = [x for x in COUNTIES if x != p.county]
    c.accident_county = far[int(rng.integers(len(far)))]
    c.nights_weekend = True
    if p.vehicle_year <= 2014:
        c.theft_flag = True
        c.loss_description = str(rng.choice(GEO_DESCRIPTIONS))


def inject_ring(
    rng: np.random.Generator, c: Claim, p: Policy, ring: Ring,
    policies_by_id: dict[str, Policy], ref_date: date,
) -> list[Claim]:
    """Claim joins the ring (shared entities), and a linked 'history' claim is
    created on another member policy within the preceding 90 days - dense
    shared-entity signal, exactly what ring detection features key on."""
    c.ring_id = ring.ring_id
    c.garage_id = ring.garage_id
    c.loss_description = str(rng.choice(RING_DESCRIPTIONS))
    if p.policy_id not in ring.member_policy_ids:
        ring.member_policy_ids.append(p.policy_id)

    other_id = str(rng.choice([m for m in ring.member_policy_ids if m != p.policy_id]))
    mp = policies_by_id[other_id]
    window_start = max(mp.inception_date + timedelta(days=21), c.loss_date - timedelta(days=90))
    if mp.expiry_date <= window_start:
        return []
    loss = window_start + timedelta(days=int(rng.integers(0, max((c.loss_date - window_start).days, 1))))
    amount = min(
        float(np.random.default_rng(int(rng.integers(0, 2**31))).lognormal(
            np.log(0.30 * mp.vehicle_value) - SEVERITY_SIGMA**2 / 2, SEVERITY_SIGMA)),
        mp.sum_insured,
    )
    support = Claim(
        policy_id=other_id, loss_date=loss,
        reported_date=loss + timedelta(days=1),
        claim_amount=round(amount, 2),
        repair_estimate=round(amount * float(rng.uniform(1.1, 1.6)), 2),
        book_value_cost=round(amount * float(rng.uniform(0.9, 1.1)), 2),
        garage_id=ring.garage_id, accident_county=mp.county,
        loss_description=str(rng.choice(RING_DESCRIPTIONS)),
        ring_id=ring.ring_id, is_fraud_label=True, typology="RING",
    )
    return [support]


def inject_fraud(
    rng: np.random.Generator, claims: list[Claim],
    policies_by_id: dict[str, Policy], rings: list[Ring],
    rate: float, ref_date: date,
) -> list[Claim]:
    n_fraud = int(len(claims) * rate)
    idxs = rng.choice(len(claims), size=min(n_fraud, len(claims)), replace=False)
    for i in idxs:
        c = claims[int(i)]
        p = policies_by_id[c.policy_id]
        t = TYPOLOGIES[int(rng.choice(4, p=WEIGHTS))]
        if t == "EARLY_CLAIM":
            inject_early_claim(rng, c, p)
        elif t == "INFLATION":
            inject_inflation(rng, c, p)
        elif t == "GEO_ANOMALY":
            inject_geo_anomaly(rng, c, p)
        else:
            claims.extend(inject_ring(
                rng, c, p, rings[int(rng.integers(len(rings)))], policies_by_id, ref_date))
        c.is_fraud_label = True
        c.typology = t
    return claims
