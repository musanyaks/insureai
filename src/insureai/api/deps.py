"""FastAPI dependency wiring. Route functions never touch app.state directly -
they declare what they need and get it injected, which keeps them testable."""
from __future__ import annotations

from typing import Annotated, Protocol

from fastapi import Depends, Request
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from insureai.audit.trail import AuditTrail
from insureai.config import Settings, get_settings
from insureai.schemas.envelope import AgentEnvelope


class Bus(Protocol):
    """Minimal contract both InMemoryBus and KafkaBus satisfy."""
    def publish(self, envelope: AgentEnvelope, topic: str = "") -> None: ...
    def subscribe(self, agent: str, handler) -> None: ...


def get_settings_dep() -> Settings:
    return get_settings()


def get_pool(request: Request) -> ConnectionPool:
    return request.app.state.pool


def get_bus(request: Request) -> Bus:
    return request.app.state.bus


def get_audit(request: Request) -> AuditTrail:
    return request.app.state.audit


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
PoolDep = Annotated[ConnectionPool, Depends(get_pool)]
BusDep = Annotated[Bus, Depends(get_bus)]
AuditDep = Annotated[AuditTrail, Depends(get_audit)]

# psycopg_pool passes kwargs to every connection it opens - dict rows everywhere.
POOL_KWARGS = {"row_factory": dict_row}
