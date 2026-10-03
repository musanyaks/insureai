-- INSUREAI v1 schema. Relational + vector in one engine (ADR-001: pgvector over Qdrant).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE policies (
    policy_id        TEXT PRIMARY KEY,
    customer_name    TEXT NOT NULL,
    phone            TEXT,
    bank_account     TEXT,
    id_number        TEXT,
    vehicle_make     TEXT NOT NULL,
    vehicle_model    TEXT NOT NULL,
    vehicle_year     INT  NOT NULL,
    vehicle_value    NUMERIC(12,2) NOT NULL,
    sum_insured      NUMERIC(12,2) NOT NULL,
    annual_premium   NUMERIC(12,2) NOT NULL,
    county           TEXT NOT NULL,
    inception_date   DATE NOT NULL,
    expiry_date      DATE NOT NULL,
    status           TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE claims (
    claim_id           TEXT PRIMARY KEY,
    policy_id          TEXT NOT NULL REFERENCES policies(policy_id),
    loss_date          DATE NOT NULL,
    reported_date      DATE NOT NULL,
    claim_amount       NUMERIC(12,2) NOT NULL,
    repair_estimate    NUMERIC(12,2),
    book_value_cost    NUMERIC(12,2),
    garage_id          TEXT,
    accident_county    TEXT NOT NULL,
    loss_description   TEXT,
    theft_flag         BOOLEAN NOT NULL DEFAULT false,
    nights_weekend     BOOLEAN NOT NULL DEFAULT false,
    is_fraud_label     BOOLEAN,          -- ground truth (synthetic); NULL = unscored real data
    typology           TEXT,             -- injected pattern, if any
    status             TEXT NOT NULL DEFAULT 'INTAKE',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_claims_policy ON claims(policy_id);
CREATE INDEX idx_claims_fraud  ON claims(is_fraud_label) WHERE is_fraud_label;

-- Shared-entity links (phone / bank / ID / garage) - the substrate for ring detection
CREATE TABLE claim_entities (
    entity_type   TEXT NOT NULL CHECK (entity_type IN ('PHONE','BANK','ID','GARAGE')),
    entity_value  TEXT NOT NULL,
    claim_id      TEXT NOT NULL REFERENCES claims(claim_id),
    PRIMARY KEY (entity_type, entity_value, claim_id)
);
CREATE INDEX idx_entities_value ON claim_entities(entity_type, entity_value);

-- Append-only agent communication audit (ADR-004: audit rows are never updated)
CREATE TABLE agent_messages (
    id             BIGSERIAL PRIMARY KEY,
    task_id        TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    from_agent     TEXT NOT NULL,
    to_agent       TEXT NOT NULL,
    event          TEXT NOT NULL,
    priority       TEXT NOT NULL,
    payload        JSONB NOT NULL,
    model_version  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_corr ON agent_messages(correlation_id);

CREATE TABLE investigations (
    investigation_id TEXT PRIMARY KEY,
    claim_id         TEXT NOT NULL REFERENCES claims(claim_id),
    status           TEXT NOT NULL DEFAULT 'RUNNING',
    started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at     TIMESTAMPTZ
);

-- Human-in-the-loop gate (ADR-003: high-risk scores must stop here)
CREATE TABLE approvals (
    approval_id       BIGSERIAL PRIMARY KEY,
    investigation_id  TEXT REFERENCES investigations(investigation_id),
    fraud_probability NUMERIC(5,4),
    recommendation    TEXT,
    decision          TEXT NOT NULL DEFAULT 'PENDING'
                      CHECK (decision IN ('APPROVED','REJECTED','PENDING')),
    decided_by        TEXT,
    decided_at        TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RAG store: policy documents, claims manual, underwriting guidelines
CREATE TABLE documents (
    doc_id      TEXT NOT NULL,
    source      TEXT NOT NULL,
    chunk_index INT  NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (doc_id, chunk_index)
);

-- v0.1.1: API routes
CREATE SEQUENCE IF NOT EXISTS claim_id_seq START 100000;  -- past seeded range, no collision
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS report JSONB;  -- orchestrator writes final report here
ALTER TABLE approvals      ADD COLUMN IF NOT EXISTS note TEXT;
CREATE INDEX IF NOT EXISTS idx_investigations_claim ON investigations(claim_id);
