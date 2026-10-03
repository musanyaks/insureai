"""The typed contract for ALL agent communication. Every message on the bus is
one of these - which is what makes the system auditable end to end."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


def _new_task_id() -> str:
    return f"TASK-{uuid4().hex[:12].upper()}"


class AgentEnvelope(BaseModel):
    task_id: str = Field(default_factory=_new_task_id)
    correlation_id: str          # one investigation = one correlation_id, everywhere
    from_agent: str
    to_agent: str
    event: str                   # "claim.review_requested", "fraud.score_completed", ...
    priority: Priority = Priority.MEDIUM
    payload: dict[str, Any] = Field(default_factory=dict)
    model_version: str | None = None   # mandatory on any ML-derived output
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    audit: bool = True

    def reply(self, event: str, payload: dict[str, Any]) -> "AgentEnvelope":
        return AgentEnvelope(
            correlation_id=self.correlation_id,
            from_agent=self.to_agent,
            to_agent=self.from_agent,
            event=event,
            priority=self.priority,
            payload=payload,
        )
