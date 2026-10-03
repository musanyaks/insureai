"""Dev/test bus: identical interface to KafkaBus, zero external deps.
Integration tests run the whole agent fleet through this."""
from collections import defaultdict
from typing import Callable

from insureai.schemas.envelope import AgentEnvelope

Handler = Callable[[AgentEnvelope], None]


class InMemoryBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self.published: list[tuple[str, AgentEnvelope]] = []

    def subscribe(self, agent: str, handler: Handler) -> None:
        self._handlers[agent].append(handler)

    def publish(self, envelope: AgentEnvelope, topic: str = "") -> None:
        self.published.append((topic, envelope))
        for h in self._handlers.get(envelope.to_agent, []):
            h(envelope)
