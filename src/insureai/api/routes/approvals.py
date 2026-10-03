"""The human-in-the-loop gate (ADR-003). Decisions are officer-only, a PENDING
approval can be decided exactly once (409 on replay), the claim status follows
the decision in the same transaction, and the human action enters the SAME
agent_messages audit stream as a machine envelope - from_agent 'human:<sub>'.
That single design choice is what makes the audit trail complete."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from insureai.api.deps import AuditDep, PoolDep
from insureai.api.middleware.auth import Role, require_roles
from insureai.schemas.envelope import AgentEnvelope, Priority

router = APIRouter(prefix="/approvals", tags=["approvals"])

Viewer = require_roles(Role.VIEWER)
Officer = require_roles(Role.OFFICER)


class DecisionRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    note: str | None = Field(None, max_length=2000)


@router.get("")
def list_approvals(
    pool: PoolDep,
    _: object = Depends(Viewer),
    decision: str | None = Query(None, description="PENDING/APPROVED/REJECTED"),
    limit: int = Query(50, le=200),
):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.approval_id, a.investigation_id, a.fraud_probability,
                   a.recommendation, a.decision, a.decided_by, a.decided_at,
                   a.created_at, a.note,
                   i.claim_id, c.claim_amount, c.loss_description
            FROM approvals a
            LEFT JOIN investigations i USING (investigation_id)
            LEFT JOIN claims c USING (claim_id)
            WHERE (%(d)s::text IS NULL OR a.decision = %(d)s)
            ORDER BY a.created_at DESC
            LIMIT %(limit)s
            """,
            {"d": decision, "limit": limit},
        )
        rows = cur.fetchall()
    return {"items": rows}


@router.get("/{approval_id}")
def get_approval(approval_id: int, pool: PoolDep, _: object = Depends(Viewer)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM approvals WHERE approval_id = %s", (approval_id,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="approval not found")
    return row


@router.post("/{approval_id}/decision")
def decide(approval_id: int, body: DecisionRequest, pool: PoolDep,
           audit: AuditDep, user=Depends(Officer)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT approval_id, investigation_id, decision, fraud_probability, "
            "recommendation FROM approvals WHERE approval_id = %s FOR UPDATE",
            (approval_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="approval not found")
        if row["decision"] != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"approval already decided ({row['decision']}) - decisions are immutable",
            )

        cur.execute(
            "UPDATE approvals SET decision = %s, decided_by = %s, "
            "decided_at = now(), note = %s WHERE approval_id = %s",
            (body.decision, user.sub, body.note, approval_id),
        )
        cur.execute(
            "UPDATE claims SET status = %s "
            "WHERE claim_id = (SELECT claim_id FROM investigations "
            "                  WHERE investigation_id = %s)",
            (body.decision, row["investigation_id"]),
        )

    env = AgentEnvelope(
        correlation_id=row["investigation_id"],
        from_agent=f"human:{user.sub}",          # humans are first-class in the audit
        to_agent="orchestrator",
        event="approval.decided",
        priority=Priority.HIGH,
        payload={
            "approval_id": approval_id,
            "decision": body.decision,
            "note": body.note,
            "fraud_probability": float(row["fraud_probability"]) if row["fraud_probability"] else None,
            "recommendation": row["recommendation"],
        },
    )
    audit.record(env)

    return {"approval_id": approval_id, "decision": body.decision,
            "decided_by": user.sub, "claim_status": body.decision}
