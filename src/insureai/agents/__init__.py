"""Agent fleet wiring. register_agents() is called by:
  - the Kafka worker (compose) — fleet runs as its own service, or
  - the API lifespan when BUS_BACKEND=memory AND INLINE_AGENTS=1 —
    single-process local demo where the whole pipeline runs inline."""
from __future__ import annotations


def register_agents(bus, audit=None):
    if getattr(bus, "_insureai_agents", False):   # idempotent
        return []
    from insureai.agents.claims.agent import ClaimsAgent
    from insureai.agents.fraud.agent import FraudAgent
    from insureai.agents.orchestrator.agent import OrchestratorAgent
    from insureai.config import get_settings

    dsn = get_settings().dsn
    fleet = [
        OrchestratorAgent(bus, audit, dsn=dsn),
        ClaimsAgent(bus, audit, dsn=dsn),
        FraudAgent(bus, audit),
    ]
    bus._insureai_agents = True
    return fleet