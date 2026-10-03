"""Claim read + intake. POST /claims is the entry point of the whole system:
it persists the claim and publishes claim.registered - the orchestrator (Phase 1)
subscribes to that event and decides the pipeline. The API deliberately does
NOT know which agents exist."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from insureai.api.deps import AuditDep, BusDep, PoolDep
from insureai.api.middleware.auth import Role, require_roles
from insureai.schemas.claim import ClaimCreate
from insureai.schemas.envelope import AgentEnvelope

router = APIRouter(prefix="/claims", tags=["claims"])

Viewer = require_roles(Role.VIEWER)
Officer = require_roles(Role.OFFICER)


@router.get("")
def list_claims(
    pool: PoolDep,
    _: object = Depends(Viewer),
    status_filter: str | None = Query(None, alias="status"),
    county: str | None = None,
    fraud: bool | None = Query(None, description="None=all, true=flagged, false=clean"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    where = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}
    if status_filter:
        where.append("c.status = %(status)s")
        params["status"] = status_filter
    if county:
        where.append("p.county = %(county)s")
        params["county"] = county
    if fraud is not None:
        where.append("c.is_fraud_label = %(fraud)s")
        params["fraud"] = fraud
    clause = " AND ".join(where)

    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS n FROM claims c JOIN policies p USING (policy_id) WHERE {clause}",
            params,
        )
        total = cur.fetchone()["n"]
        cur.execute(
            f"""
            SELECT c.claim_id, c.policy_id, c.loss_date, c.reported_date,
                   c.claim_amount, c.status, c.is_fraud_label, c.typology,
                   p.county, p.vehicle_make, p.vehicle_model
            FROM claims c JOIN policies p USING (policy_id)
            WHERE {clause}
            ORDER BY c.created_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        rows = cur.fetchall()
    return {"total": total, "limit": limit, "offset": offset, "items": rows}


@router.get("/{claim_id}")
def get_claim(claim_id: str, pool: PoolDep, _: object = Depends(Viewer)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.*, p.vehicle_make, p.vehicle_model, p.county AS policy_county,
                   p.sum_insured, p.inception_date, p.expiry_date, p.status AS policy_status
            FROM claims c JOIN policies p USING (policy_id)
            WHERE c.claim_id = %s
            """,
            (claim_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="claim not found")
    return row


@router.get("/{claim_id}/entities")
def claim_entities(claim_id: str, pool: PoolDep, _: object = Depends(Viewer)):
    """Shared-entity links for this claim, with counts of OTHER claims sharing
    each identifier. This is the ring-detection substrate the fraud features
    count - exposed here so the UI can render the link network."""
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT m.entity_type, m.entity_value,
                   (SELECT COUNT(*) FROM claim_entities x
                     WHERE x.entity_type = m.entity_type
                       AND x.entity_value = m.entity_value
                       AND x.claim_id <> %s) AS other_links,
                   (SELECT COUNT(*) FROM claim_entities x
                      JOIN claims c2 USING (claim_id)
                     WHERE x.entity_type = m.entity_type
                       AND x.entity_value = m.entity_value
                       AND x.claim_id <> %s
                       AND c2.is_fraud_label) AS other_fraud_links
            FROM claim_entities m
            WHERE m.claim_id = %s
            ORDER BY other_links DESC
            """,
            (claim_id, claim_id, claim_id),
        )
        rows = cur.fetchall()
    return {"claim_id": claim_id, "entities": rows}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_claim(body: ClaimCreate, pool: PoolDep, bus: BusDep, audit: AuditDep,
                 user: object = Depends(Officer)):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT policy_id, status, inception_date, expiry_date "
            "FROM policies WHERE policy_id = %s",
            (body.policy_id,),
        )
        policy = cur.fetchone()
        if policy is None:
            raise HTTPException(status_code=404, detail="policy not found")
        if not (policy["inception_date"] <= body.loss_date <= policy["expiry_date"]):
            # Deterministic gate, not an agent judgment: out-of-period losses go
            # to manual handling until the claims agent owns edge-case routing.
            raise HTTPException(
                status_code=422,
                detail="loss date outside policy period - requires manual review",
            )

        cur.execute("SELECT nextval('claim_id_seq') AS n")
        seq = cur.fetchone()["n"]
        claim_id = f"CLM-{body.loss_date.year}-{seq:06d}"

        cur.execute(
            """
            INSERT INTO claims (claim_id, policy_id, loss_date, reported_date,
                claim_amount, repair_estimate, book_value_cost, garage_id,
                accident_county, loss_description, theft_flag, nights_weekend, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'INTAKE')
            RETURNING claim_id, policy_id, loss_date, reported_date, claim_amount,
                repair_estimate, book_value_cost, garage_id, accident_county,
                loss_description, theft_flag, nights_weekend, status
            """,
            (claim_id, body.policy_id, body.loss_date, body.reported_date,
             body.claim_amount, body.repair_estimate, body.book_value_cost,
             body.garage_id, body.accident_county, body.loss_description,
             body.theft_flag, body.nights_weekend),
        )
        row = cur.fetchone()

    # Outside the DB transaction: an intake event is emitted even if agents
    # are down - Kafka/audit retain it, and the orchestrator catches up.
    env = AgentEnvelope(
        correlation_id=claim_id,
        from_agent="api",
        to_agent="orchestrator",
        event="claim.registered",
        payload={"claim_id": claim_id, "source": "api_intake",
                 "requested_by": getattr(user, "sub", None)},
    )
    bus.publish(env)
    audit.record(env)
    return row
