"""API factory: lifespan wires pool + bus + audit into app.state, routers and
middleware are registered here. Agents register themselves into the SAME bus in
Phase 1 via register_agents() - no API changes needed when they land."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import ConnectionPool

from insureai.api.deps import POOL_KWARGS
from insureai.api.middleware.audit import RequestAuditMiddleware
from insureai.api.middleware.auth import AuthMiddleware, Role, mint_token
from insureai.api.routes import approvals, chat, claims, investigations
from insureai.audit.trail import AuditTrail
from insureai.bus.inmemory import InMemoryBus
from insureai.bus.kafka import KafkaBus
from insureai.config import get_settings

logging.basicConfig(level=logging.INFO)

AGENT_ROSTER = ["orchestrator", "claims", "fraud", "actuarial", "sql"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    app.state.settings = s
    app.state.pool = ConnectionPool(s.dsn, min_size=1, max_size=5,
                                    kwargs=POOL_KWARGS, open=True)
    app.state.audit = AuditTrail(s.dsn)
    app.state.bus = (KafkaBus(s.kafka_bootstrap) if s.bus_backend == "kafka"
                     else InMemoryBus())
    # Phase 1 hook - orchestrator/claims/fraud/actuarial/sql agents subscribe
    # here and an in-process dispatcher consumes the bus:
    # register_agents(app.state.bus, app.state.audit)
    yield
    close = getattr(app.state.bus, "close", None)
    if close:
        close()
    app.state.pool.close()


app = FastAPI(title="INSUREAI API", version="0.1.0", lifespan=lifespan)

# Middleware order: CORS outermost (last added), then request audit, then auth -
# so CORS headers appear even on 401s, and 401s are still audited.
s = get_settings()
app.add_middleware(AuthMiddleware, secret=s.jwt_secret)
app.add_middleware(RequestAuditMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=s.cors_origin_list,
                   allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

app.include_router(claims.router)
app.include_router(investigations.router)
app.include_router(approvals.router)
app.include_router(chat.router)


def _check_kafka(bootstrap: str) -> bool:
    try:
        from confluent_kafka import Consumer
        c = Consumer({"bootstrap.servers": bootstrap, "group.id": "healthcheck"})
        c.list_topics(timeout=2)
        c.close()
        return True
    except Exception:
        return False


@app.get("/health")
def health():
    checks: dict[str, bool] = {}
    try:
        with app.state.pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        checks["db"] = True
    except Exception:
        checks["db"] = False
    checks["kafka"] = s.bus_backend != "kafka" or _check_kafka(s.kafka_bootstrap)
    return {"status": "ok" if all(checks.values()) else "degraded",
            "environment": s.environment, "checks": checks, "agents": AGENT_ROSTER}


if s.environment == "dev":
    @app.post("/auth/dev-token", tags=["auth"])
    def dev_token(body: dict):
        """Dev-only token minting so the demo works without an IdP."""
        sub = body.get("sub", "demo-user")
        roles = [r for r in body.get("roles", ["viewer"]) if r in Role._value2member_map_]
        return {"access_token": mint_token(sub, [Role(r) for r in roles], s.jwt_secret),
                "token_type": "bearer"}
