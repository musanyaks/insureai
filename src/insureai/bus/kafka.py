"""Kafka bus (Redpanda in dev). v1 topology: a single commands topic with
in-process dispatch by `to_agent` - correct because all agents share one process.
Scale-out path (per-agent consumer groups) documented in ADR-002.

Key = correlation_id, so every message of one investigation lands on the same
partition, in order. That property is what the audit trail relies on."""
import logging
from typing import Callable

from confluent_kafka import Consumer, Producer

from insureai.bus.topics import Topics
from insureai.schemas.envelope import AgentEnvelope

logger = logging.getLogger(__name__)
Handler = Callable[[AgentEnvelope], None]


class KafkaBus:
    def __init__(self, bootstrap: str) -> None:
        self._bootstrap = bootstrap
        self._producer = Producer({"bootstrap.servers": bootstrap})
        self._consumer: Consumer | None = None
        self._handlers: dict[str, Handler] = {}

    def subscribe(self, agent: str, handler: Handler) -> None:
        self._handlers[agent] = handler

    def publish(self, envelope: AgentEnvelope, topic: str = Topics.COMMANDS) -> None:
        self._producer.produce(
            topic, key=envelope.correlation_id, value=envelope.model_dump_json()
        )
        self._producer.poll(0)

    def run(self) -> None:
        self._consumer = Consumer({
            "bootstrap.servers": self._bootstrap,
            "group.id": "insureai-dispatcher",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self._consumer.subscribe([Topics.COMMANDS])
        logger.info("bus running - agents: %s", list(self._handlers))
        try:
            while True:
                msg = self._consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.warning("kafka error: %s", msg.error())
                    continue
                env = AgentEnvelope.model_validate_json(msg.value())
                handler = self._handlers.get(env.to_agent)
                if handler is None:
                    logger.warning("no handler registered for '%s'", env.to_agent)
                    continue
                handler(env)
                self._consumer.commit(msg)
        except KeyboardInterrupt:
            pass
        finally:
            self.close()

    def close(self) -> None:
        if self._consumer:
            self._consumer.close()
        self._producer.flush(10)
