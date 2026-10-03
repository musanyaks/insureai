"""Investigation lifecycle + agent trace. The trace endpoint is what the
dashboard renders as the live agent conversation: every envelope with the
investigation's correlation_id, in order, from agent_messages."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from insureai.api.deps import AuditDep, BusDep, PoolDep
from insureai.api.middleware.auth import Role, require_roles
from insureai.api.services import start_investigation

router = APIRouter(prefix="/investigations", tags=["investigations"])

Viewer = require_roles(Role.VIEWER)
Officer = require_roles(Role.OFFICER)


@router.post("", status_code=202)
def start(body: dict, pool: PoolDep, bus: BusDep, audit: AuditDep,
          user=Depends(Officer)):
    """202 Accepted - investigation starts asynchronously via the agent bus."""
    claim_id = (body or {}).get("claim_id", "")
    if not claim_id:
        raise HTTPException(status_code=422, detail="claim_id is required")
    result = start_investigation(
        pool, bus, audit, claim_id=claim_id,
        trigger="manual", requested_by=getattr(user, "sub", None),
    )
    if result is None:
        raise HTTPException(status_code=404, detail="claim not found")
    return result


@router.get("")
def list_investigations(
    pool: PoolDep,
    _: object = Depends(Viewer),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT i.investigation_id, i.claim_id, i.status, i.started_at,
                   i.completed_at, c.claim_amount
            FROM investigations i JOIN claims c USING (claim_id)
            WHERE (%(status)s::text IS NULL OR i.status = %(status)s)
            ORDER BY i.started_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            {"status": status_filter, "limit": limit, "offset": offset},
        )
        rows = cur.fetchall()
    return {"items": rows}


@router.get("/{investigation_id}")
def get_investigation(investigation_id: str, pool: PoolDep,
                      _: object = Depends(Viewer)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT i.*, a.approval_id, a.decision AS approval_decision,
                   a.fraud_probability, a.recommendation
            FROM investigations i
            LEFT JOIN approvals a USING (investigation_id)
            WHERE i.investigation_id = %s
            """,
            (investigation_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="investigation not found")
    return row


@router.get("/{investigation_id}/trace")
def investigation_trace(investigation_id: str, pool: PoolDep,
                        _: object = Depends(Viewer)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT investigation_id FROM investigations WHERE investigation_id = %s",
            (investigation_id,),
        )
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="investigation not found")
        cur.execute(
            """
            SELECT task_id, from_agent, to_agent, event, priority,
                   payload, model_version, created_at
            FROM agent_messages
            WHERE correlation_id = %s
            ORDER BY id
            """,
            (investigation_id,),
        )
        rows = cur.fetchall()
    return {"investigation_id": investigation_id, "messages": rows}
