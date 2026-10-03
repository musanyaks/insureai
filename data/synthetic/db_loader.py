"""Bulk load via COPY. TRUNCATE ... CASCADE keeps re-seeding idempotent."""
import psycopg

from data.synthetic.claims import Claim
from data.synthetic.policies import Policy

POLICY_COLS = ("policy_id, customer_name, phone, bank_account, id_number, vehicle_make, "
               "vehicle_model, vehicle_year, vehicle_value, sum_insured, annual_premium, "
               "county, inception_date, expiry_date, status")
CLAIM_COLS = ("claim_id, policy_id, loss_date, reported_date, claim_amount, repair_estimate, "
              "book_value_cost, garage_id, accident_county, loss_description, theft_flag, "
              "nights_weekend, is_fraud_label, typology, status")


def _policy_row(p: Policy) -> tuple:
    return (p.policy_id, p.customer_name, p.phone, p.bank_account, p.id_number,
            p.vehicle_make, p.vehicle_model, p.vehicle_year, p.vehicle_value,
            p.sum_insured, p.annual_premium, p.county, p.inception_date,
            p.expiry_date, p.status)


def _claim_row(c: Claim) -> tuple:
    return (c.claim_id, c.policy_id, c.loss_date, c.reported_date, c.claim_amount,
            c.repair_estimate, c.book_value_cost, c.garage_id, c.accident_county,
            c.loss_description, c.theft_flag, c.nights_weekend, c.is_fraud_label,
            c.typology, "INTAKE")


def load_all(dsn: str, policies, claims, entities) -> None:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE claim_entities, claims, policies RESTART IDENTITY CASCADE")
        with cur.copy(f"COPY policies ({POLICY_COLS}) FROM STDIN") as cp:
            for p in policies:
                cp.write_row(_policy_row(p))
        with cur.copy(f"COPY claims ({CLAIM_COLS}) FROM STDIN") as cp:
            for c in claims:
                cp.write_row(_claim_row(c))
        with cur.copy("COPY claim_entities (entity_type, entity_value, claim_id) FROM STDIN") as cp:
            for e in entities:
                cp.write_row(e)
    print(f"loaded: {len(policies)} policies, {len(claims)} claims, {len(entities)} entity links")
