"""Dashboard read-model. Every number the UI displays must be a real query
result — same principle as ADR-003 (numbers never come from generated text),
applied to the frontend."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from insureai.api.deps import PoolDep
from insureai.api.middleware.auth import Role, require_roles

router = APIRouter(prefix="/analytics", tags=["analytics"])
Viewer = require_roles(Role.VIEWER)


@router.get("/summary")
def summary(pool: PoolDep, _: object = Depends(Viewer)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
              (SELECT COUNT(*) FROM policies)                                  AS policies,
              (SELECT COUNT(*) FROM claims)                                    AS claims,
              (SELECT COALESCE(SUM(claim_amount), 0) FROM claims)              AS claims_value,
              (SELECT COUNT(*) FROM investigations WHERE status = 'RUNNING')   AS investigations_running,
              (SELECT COUNT(*) FROM investigations
                WHERE status = 'AWAITING_APPROVAL')                            AS awaiting_approval,
              (SELECT COUNT(*) FROM investigations
                WHERE report->>'risk_level' = 'HIGH')                          AS high_risk,
              (SELECT COUNT(*) FROM investigations
                WHERE report->>'risk_level' IN ('HIGH', 'MEDIUM'))             AS fraud_alerts,
              (SELECT COUNT(*) FROM agent_messages
                WHERE created_at > now() - interval '24 hours')                AS agent_events_24h
        """)
        return cur.fetchone()


@router.get("/county-risk")
def county_risk(pool: PoolDep, _: object = Depends(Viewer)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT p.county,
                   COUNT(c.claim_id)                                        AS claims,
                   COUNT(*) FILTER (WHERE c.is_fraud_label)                 AS fraud_claims,
                   ROUND(COUNT(*) FILTER (WHERE c.is_fraud_label)::numeric
                         / NULLIF(COUNT(c.claim_id), 0), 3)                 AS fraud_rate,
                   COALESCE(SUM(c.claim_amount), 0)                         AS claims_value
            FROM claims c JOIN policies p USING (policy_id)
            GROUP BY p.county
        """)
        rows = cur.fetchall()
    for r in rows:
        rate = float(r["fraud_rate"] or 0)
        r["risk_level"] = ("VERY HIGH" if rate >= 0.15 else "HIGH" if rate >= 0.10
                           else "MEDIUM" if rate >= 0.07 else "LOW")
    return {"items": rows}


@router.get("/claims-trend")
def claims_trend(pool: PoolDep, _: object = Depends(Viewer),
                 months: int = Query(6, le=24)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT to_char(date_trunc('month', loss_date), 'Mon YYYY')  AS month,
                   COUNT(*)                                             AS claims,
                   COUNT(*) FILTER (WHERE is_fraud_label)               AS fraudulent
            FROM claims
            WHERE loss_date >= date_trunc('month', now())
                  - ((%s::int) || ' months')::interval
            GROUP BY 1, date_trunc('month', loss_date)
            ORDER BY date_trunc('month', loss_date)
        """, (months,))
        return {"items": cur.fetchall()}


@router.get("/agent-activity")
def agent_activity(pool: PoolDep, _: object = Depends(Viewer),
                   limit: int = Query(30, le=100)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT from_agent, to_agent, event, priority, correlation_id,
                   payload->>'claim_id' AS claim_id, created_at
            FROM agent_messages
            ORDER BY id DESC LIMIT %s
        """, (limit,))
        return {"items": cur.fetchall()}


@router.get("/fraud-alerts")
def fraud_alerts(pool: PoolDep, _: object = Depends(Viewer),
                 limit: int = Query(10, le=50)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT i.investigation_id, i.claim_id, c.claim_amount, i.status,
                   i.started_at,
                   (i.report->>'fraud_probability')::float  AS fraud_probability,
                   i.report->>'risk_level'                  AS risk_level
            FROM investigations i JOIN claims c USING (claim_id)
            WHERE i.report IS NOT NULL
            ORDER BY (i.report->>'fraud_probability')::float DESC NULLS LAST
            LIMIT %s
        """, (limit,))
        return {"items": cur.fetchall()}



@router.get("/typologies")
def typologies(pool: PoolDep, _: object = Depends(Viewer)):
    """Claims distribution by fraud typology (CLEAN = no injected pattern)."""
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(typology, 'CLEAN') AS typology, COUNT(*) AS claims
            FROM claims GROUP BY 1 ORDER BY 2 DESC
        """)
        return {"items": cur.fetchall()}
