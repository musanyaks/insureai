"""Entry point:  python -m data.synthetic.generate --policies 20000 --fraud-rate 0.08

Deterministic under --seed (default 42). Writes CSVs to data/seed/, the golden
set to evals/golden_claims.csv, and optionally loads Postgres."""
import argparse
import os
from datetime import date

import numpy as np
import pandas as pd

from data.synthetic.claims import build_entities, generate_claims
from data.synthetic.policies import generate_policies
from data.synthetic.typologies import create_rings, inject_fraud

REF_DATE = date(2026, 9, 30)


def build_dataset(n_policies: int, fraud_rate: float, seed: int):
    rng = np.random.default_rng(seed)
    policies = generate_policies(n_policies, rng, REF_DATE)
    claims = generate_claims(policies, rng, REF_DATE)
    rings = create_rings(policies, rng)
    claims = inject_fraud(rng, claims, {p.policy_id: p for p in policies}, rings, fraud_rate, REF_DATE)

    # IDs assigned AFTER typologies - loss dates may have shifted
    for i, c in enumerate(claims, start=1):
        c.claim_id = f"CLM-{c.loss_date.year}-{i:06d}"

    rings_by_id = {r.ring_id: r for r in rings}
    entities = build_entities(policies, claims, rings_by_id)
    return policies, claims, entities


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policies", type=int, default=20_000)
    ap.add_argument("--fraud-rate", type=float, default=0.08)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--load-db", action="store_true")
    args = ap.parse_args()

    policies, claims, entities = build_dataset(args.policies, args.fraud_rate, args.seed)

    os.makedirs("data/seed", exist_ok=True)
    pd.DataFrame([p.__dict__ for p in policies]).to_csv("data/seed/policies.csv", index=False)
    pd.DataFrame([c.__dict__ for c in claims]).to_csv("data/seed/claims.csv", index=False)
    pd.DataFrame(entities, columns=["entity_type", "entity_value", "claim_id"]).to_csv(
        "data/seed/claim_entities.csv", index=False)

    os.makedirs("evals", exist_ok=True)
    golden = pd.DataFrame([{"claim_id": c.claim_id,
                            "is_fraud_label": int(c.is_fraud_label),
                            "typology": c.typology or "NONE"} for c in claims])
    golden.to_csv("evals/golden_claims.csv", index=False)

    fraud = [c for c in claims if c.is_fraud_label]
    print(f"policies={len(policies)}  claims={len(claims)}  fraud={len(fraud)} "
          f"({len(fraud)/len(claims):.1%})  entities={len(entities)}")
    print(pd.Series([c.typology for c in fraud]).value_counts().to_string())
    print(f"mean severity - fraud: {np.mean([c.claim_amount for c in fraud]):,.0f} | "
          f"clean: {np.mean([c.claim_amount for c in claims if not c.is_fraud_label]):,.0f}")

    if args.load_db:
        from data.synthetic.db_loader import load_all
        from insureai.config import get_settings
        load_all(get_settings().dsn, policies, claims, entities)


if __name__ == "__main__":
    main()
