"""BaseAgent owns every cross-cutting concern: routing check, audit, error
containment. Subclasses implement exactly one thing: handle().
An agent that raises must never crash the bus - it returns an error envelope."""
from __future__ import annotations

from abc import ABC, abstractmethod

from insureai.audit.trail import AuditTrail
from insureai.bus.topics import Topics
from insureai.schemas.envelope import AgentEnvelope


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, bus, audit: AuditTrail | None = None) -> None:
        self.bus = bus
        self.audit = audit
        bus.subscribe(self.name, self)

    def __call__(self, envelope: AgentEnvelope) -> None:
        if envelope.to_agent != self.name:
            return
        if self.audit:
            self.audit.record(envelope)
        try:
            reply = self.handle(envelope)
            if reply is not None:
                self.bus.publish(reply, topic=Topics.RESULTS)
        except Exception as exc:  # containment, not silence - the error is on the bus
            self.bus.publish(
                envelope.reply("agent.error", {"error": repr(exc), "agent": self.name}),
                topic=Topics.RESULTS,
            )

    @abstractmethod
    def handle(self, envelope: AgentEnvelope) -> AgentEnvelope | None:
        """Return a reply envelope (published to RESULTS) or None."""
