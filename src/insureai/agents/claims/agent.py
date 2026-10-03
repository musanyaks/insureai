"""Claims Intelligence Agent (v1): assembles the structured claim context the
rest of the pipeline scores against — claim + policy, trailing-12m history,
shared-entity links. Pure deterministic reads; it emits facts, not opinions.
Document extraction arrives with the Document Agent; LLM-assisted intake
normalization plugs in at the same point."""
from __future__ import annotations

from insureai.agents.base import BaseAgent
from insureai.db import clean_row, get_conn

CLAIM_QUERY = """
    SELECT c.claim_id, c.policy_id, c.loss_date, c.reported_date, c.claim_amount,
           c.repair_estimate, c.book_value_cost, c.garage_id, c.accident_county,
           c.loss_description, c.theft_flag, c.nights_weekend,
           p.vehicle_make, p.vehicle_model, p.vehicle_year, p.vehicle_value,
           p.sum_insured, p.county AS policy_county, p.inception_date
    FROM claims c JOIN policies p USING (policy_id)
    WHERE c.claim_id = %s
"""

PRIOR_QUERY = """
    SELECT COUNT(*) AS n, COALESCE(SUM(claim_amount), 0) AS total
    FROM claims
    WHERE policy_id = %s AND claim_id <> %s
      AND loss_date >= %s - INTERVAL '365 days' AND loss_date <= %s
"""

# Entity links count OTHER POLICIES only — a customer's own second claim must
# not read as a ring signal.
ENTITY_QUERY = """
    SELECT m.entity_type, m.entity_value,
           (SELECT COUNT(*) FROM claim_entities x JOIN claims c2 USING (claim_id)
             WHERE x.entity_type = m.entity_type AND x.entity_value = m.entity_value
               AND x.claim_id <> m.claim_id AND c2.policy_id <> %s) AS other_links,
           (SELECT COUNT(*) FROM claim_entities x JOIN claims c2 USING (claim_id)
             WHERE x.entity_type = m.entity_type AND x.entity_value = m.entity_value
               AND x.claim_id <> m.claim_id AND c2.policy_id <> %s
               AND c2.is_fraud_label) AS other_fraud_links
    FROM claim_entities m
    WHERE m.claim_id = %s
"""


class ClaimsAgent(BaseAgent):
    name = "claims"

    def __init__(self, bus, audit=None, dsn: str | None = None) -> None:
        super().__init__(bus, audit)
        self.dsn = dsn

    def handle(self, envelope):
        if envelope.event != "claim.context_requested":
            return None
        claim_id = str(envelope.payload.get("claim_id", ""))
        return envelope.reply("claim.context", self._build_context(claim_id))

    def _build_context(self, claim_id: str) -> dict:
        with get_conn(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(CLAIM_QUERY, (claim_id,))
            claim = cur.fetchone()
            if claim is None:
                return {"claim_id": claim_id, "claim": {},
                        "prior_claims_12m": {"count": 0, "total_amount": 0.0},
                        "entity_links": [], "error": "claim not found"}
            cur.execute(PRIOR_QUERY, (claim["policy_id"], claim_id,
                                      claim["loss_date"], claim["loss_date"]))
            prior = cur.fetchone()
            cur.execute(ENTITY_QUERY, (claim["policy_id"], claim["policy_id"], claim_id))
            links = cur.fetchall()
        return {
            "claim_id": claim_id,
            "claim": clean_row(claim),
            "prior_claims_12m": {"count": prior["n"], "total_amount": float(prior["total"])},
            "entity_links": [clean_row(l) for l in links],
        }