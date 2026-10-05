"""Proves the API layer works with zero agents registered: intake publishes an
envelope, investigations are idempotent, the trace is complete, the approval
gate is one-shot, and auth is enforced. Runs against compose Postgres; bus is
InMemory (default) so no Kafka needed in CI.

The policy_id fixture cascade-cleans in FK order so the module is re-runnable —
residue from a previous run (claims, investigations, approvals) is removed
before fresh fixtures are inserted."""
import psycopg
import pytest
from fastapi.testclient import TestClient

from insureai.config import get_settings


@pytest.fixture(scope="module")
def api():
    try:
        psycopg.connect(get_settings().dsn, connect_timeout=5).close()
    except Exception:
        pytest.skip("postgres not available")
    from insureai.api.main import app
    with TestClient(app) as client:
        # Audit-only consumer standing in for the orchestrator: with audit at
        # the consumption point (ADR-005), the trace is fed by the consumer.
        # The pipeline itself is covered by test_orchestrator.py.
        from insureai.agents.base import BaseAgent

        class OrchestratorSink(BaseAgent):
            name = "orchestrator"

            def handle(self, envelope):
                return None

        OrchestratorSink(client.app.state.bus, client.app.state.audit)
        yield client

@pytest.fixture(scope="module")
def token(api):
    r = api.post("/auth/dev-token", json={"sub": "tester", "roles": ["officer"]})
    assert r.status_code == 200
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def policy_id(api):
    s = get_settings()
    with psycopg.connect(s.dsn) as conn, conn.cursor() as cur:
        # FK order: approvals -> investigations -> claims -> policies
        cur.execute("""
            DELETE FROM approvals WHERE investigation_id IN (
                SELECT investigation_id FROM investigations
                WHERE claim_id IN (SELECT claim_id FROM claims
                                   WHERE policy_id = 'POL-TEST-000001'))
        """)
        cur.execute("""
            DELETE FROM investigations
            WHERE claim_id IN (SELECT claim_id FROM claims
                               WHERE policy_id = 'POL-TEST-000001')
        """)
        cur.execute("DELETE FROM claims WHERE policy_id = 'POL-TEST-000001'")
        cur.execute("DELETE FROM policies WHERE policy_id = 'POL-TEST-000001'")
        cur.execute("""
            INSERT INTO policies (policy_id, customer_name, vehicle_make, vehicle_model,
                vehicle_year, vehicle_value, sum_insured, annual_premium, county,
                inception_date, expiry_date)
            VALUES ('POL-TEST-000001','Test User','Toyota','Fielder',2020,
                    1400000,1470000,52000,'Nairobi',
                    DATE '2026-01-01', DATE '2026-12-31')""")
        conn.commit()
    return "POL-TEST-000001"


def test_mutations_require_auth(api):
    assert api.post("/investigations", json={"claim_id": "CLM-2099-000001"}).status_code == 401


def test_intake_publishes_and_investigation_is_idempotent(api, token, policy_id):
    r = api.post("/claims", headers=_h(token), json={
        "policy_id": policy_id, "loss_date": "2026-03-10", "reported_date": "2026-03-11",
        "claim_amount": 850000, "accident_county": "Nairobi",
        "loss_description": "Rear-end collision",
    })
    assert r.status_code == 201
    claim_id = r.json()["claim_id"]

    r1 = api.post("/investigations", headers=_h(token), json={"claim_id": claim_id})
    assert r1.status_code == 202
    inv = r1.json()["investigation_id"]

    r2 = api.post("/investigations", headers=_h(token), json={"claim_id": claim_id})
    assert r2.json()["investigation_id"] == inv          # idempotent
    assert r2.json()["already_running"] is True

    trace = api.get(f"/investigations/{inv}/trace", headers=_h(token)).json()
    assert any(m["event"] == "claim.review_requested" for m in trace["messages"])


def test_intake_rejects_out_of_period_loss(api, token, policy_id):
    r = api.post("/claims", headers=_h(token), json={
        "policy_id": policy_id, "loss_date": "2025-06-01", "reported_date": "2025-06-02",
        "claim_amount": 100000, "accident_county": "Nairobi",
    })
    assert r.status_code == 422


def test_approval_gate_is_one_shot_and_follows_through(api, token):
    s = get_settings()
    with psycopg.connect(s.dsn) as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO approvals (investigation_id, fraud_probability, recommendation)
            SELECT investigation_id, 0.87, 'Refer for investigation'
            FROM investigations ORDER BY started_at DESC LIMIT 1
            RETURNING approval_id""")
        aid = cur.fetchone()[0]
        conn.commit()

    r = api.post(f"/approvals/{aid}/decision", headers=_h(token),
                 json={"decision": "REJECTED", "note": "ring indicators"})
    assert r.status_code == 200 and r.json()["decision"] == "REJECTED"
    assert api.post(f"/approvals/{aid}/decision", headers=_h(token),
                    json={"decision": "APPROVED"}).status_code == 409  # immutable

    with psycopg.connect(s.dsn, row_factory=psycopg.rows.dict_row) as conn, conn.cursor() as cur:
        cur.execute("SELECT from_agent, event FROM agent_messages "
                    "WHERE payload->>'approval_id' = %s", (str(aid),))
        m = cur.fetchone()
    assert m and m["from_agent"] == "human:tester" and m["event"] == "approval.decided"


def test_chat_starts_investigation(api, token, policy_id):
    r = api.post("/claims", headers=_h(token), json={
        "policy_id": policy_id, "loss_date": "2026-04-01", "reported_date": "2026-04-02",
        "claim_amount": 1200000, "accident_county": "Nairobi",
    })
    claim_id = r.json()["claim_id"]
    c = api.post("/chat", headers=_h(token), json={"message": f"investigate claim {claim_id}"})
    assert c.status_code == 200 and c.json()["intent"] == "investigate_claim"
    assert c.json()["investigation_id"]
