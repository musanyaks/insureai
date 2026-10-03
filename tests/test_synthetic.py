"""Smoke tests for the generator. CI runs these before anything else —
if the data foundation breaks, everything downstream is meaningless."""
from data.synthetic.generate import build_dataset


def test_fraud_rate_and_typologies():
    policies, claims, entities = build_dataset(n_policies=2000, fraud_rate=0.08, seed=42)
    labeled = [c for c in claims if c.is_fraud_label is not None]
    rate = sum(1 for c in labeled if c.is_fraud_label) / len(labeled)
    assert 0.05 < rate < 0.12, f"fraud rate {rate:.2%} outside tolerance"
    typologies = {c.typology for c in claims if c.is_fraud_label}
    assert {"EARLY_CLAIM", "INFLATION", "RING", "GEO_ANOMALY"} <= typologies


def test_claims_within_active_policy_window():
    policies, claims, _ = build_dataset(n_policies=1000, fraud_rate=0.08, seed=7)
    by_id = {p.policy_id: p for p in policies}
    for c in claims:
        p = by_id[c.policy_id]
        assert p.inception_date <= c.loss_date < p.expiry_date, c.claim_id


def test_ring_claims_share_entities():
    policies, claims, entities = build_dataset(n_policies=2000, fraud_rate=0.08, seed=42)
    ring_claims = [c.claim_id for c in claims if c.ring_id]
    assert ring_claims, "no ring claims generated"
    by_type_claim = {(t, cid) for t, _, cid in entities}
    for cid in ring_claims[:20]:
        assert ("PHONE", cid) in by_type_claim
