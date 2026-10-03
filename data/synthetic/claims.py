"""Clean-claims generation: Poisson frequency (per policy, exposure-adjusted),
lognormal severity capped at sum insured. Clean repair estimates carry realistic
noise (0.85-1.15 x claim amount) so the fraud task is non-trivial, not a
perfect-separation toy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

from data.synthetic.policies import COUNTIES, COUNTY_FREQ, SEVERITY_SIGMA, Policy

CLEAN_DESCRIPTIONS = [
    "Rear-end collision at a junction",
    "Windscreen cracked by flying gravel",
    "Side swipe while parking",
    "Hail damage to bonnet and roof",
    "Collision with perimeter wall at low speed",
]


@dataclass
class Claim:
    claim_id: str = ""
    policy_id: str = ""
    loss_date: date | None = None
    reported_date: date | None = None
    claim_amount: float = 0.0
    repair_estimate: float = 0.0
    book_value_cost: float = 0.0
    garage_id: str = ""
    accident_county: str = ""
    loss_description: str = ""
    theft_flag: bool = False
    nights_weekend: bool = False
    ring_id: str | None = None          # set by ring typology
    is_fraud_label: bool | None = False
    typology: str | None = None


def _severity_draw(rng: np.random.Generator, vehicle_value: float) -> float:
    mu = np.log(0.30 * vehicle_value) - SEVERITY_SIGMA**2 / 2
    return float(rng.lognormal(mu, SEVERITY_SIGMA))


def _garages(county: str) -> list[str]:
    return [f"G-{county[:3].upper()}-{j:03d}" for j in range(1, 9)]


def _freq_rate(p: Policy) -> float:
    return COUNTY_FREQ[p.county] * (1 + 0.02 * p.vehicle_age)


def generate_claims(
    policies: list[Policy], rng: np.random.Generator, ref_date: date
) -> list[Claim]:
    claims: list[Claim] = []
    garages = {c: _garages(c) for c in COUNTIES}

    for p in policies:
        days_active = (min(ref_date, p.expiry_date) - p.inception_date).days
        if days_active <= 0:
            continue
        freq = _freq_rate(p)
        n = int(rng.poisson(freq * days_active / 365.25))
        for _ in range(n):
            days_in = int(rng.integers(0, days_active))
            loss = p.inception_date + timedelta(days=days_in)
            reported = loss + timedelta(days=int(rng.integers(0, 4)))
            amount = min(_severity_draw(rng, p.vehicle_value), p.sum_insured)
            county = p.county if rng.random() < 0.88 else COUNTIES[int(rng.integers(len(COUNTIES)))]
            claims.append(Claim(
                policy_id=p.policy_id,
                loss_date=loss, reported_date=reported,
                claim_amount=round(amount, 2),
                repair_estimate=round(amount * float(rng.uniform(0.85, 1.15)), 2),
                book_value_cost=round(amount * float(rng.uniform(0.90, 1.10)), 2),
                garage_id=str(rng.choice(garages[county])),
                accident_county=county,
                loss_description=str(rng.choice(CLEAN_DESCRIPTIONS)),
                theft_flag=bool(rng.random() < 0.04),
                nights_weekend=bool(rng.random() < 0.18),
                is_fraud_label=False,
            ))
    return claims


def build_entities(
    policies: list[Policy], claims: list[Claim],
    rings_by_id: dict,
) -> list[tuple[str, str, str]]:
    """One row per (entity, claim). Ring claims use the ring's shared phone/bank -
    that is the signal the fraud features will count."""
    by_id = {p.policy_id: p for p in policies}
    rows: set[tuple[str, str, str]] = set()
    for c in claims:
        p = by_id[c.policy_id]
        ring = rings_by_id.get(c.ring_id) if c.ring_id else None
        rows.add(("PHONE", ring.phone if ring else p.phone, c.claim_id))
        rows.add(("BANK", ring.bank_account if ring else p.bank_account, c.claim_id))
        rows.add(("ID", p.id_number, c.claim_id))
        rows.add(("GARAGE", c.garage_id, c.claim_id))
    return sorted(rows)
