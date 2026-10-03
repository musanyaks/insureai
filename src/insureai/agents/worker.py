"""Agent worker: consumes COMMANDS + RESULTS from Kafka and dispatches to the
registered fleet. Runs as its own compose service; the API stays a pure
publisher. First boot drains any backlog — investigations created before the
worker existed will complete on startup (auto.offset.reset=earliest)."""
import logging


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    from insureai.agents import register_agents
    from insureai.audit.trail import AuditTrail
    from insureai.bus.kafka import KafkaBus
    from insureai.config import get_settings

    s = get_settings()
    bus = KafkaBus(s.kafka_bootstrap)
    register_agents(bus, AuditTrail(s.dsn))
    logging.getLogger("insureai.worker").info(
        "agent fleet up — consuming %s (orchestrator, claims, fraud)", s.kafka_bootstrap)
    bus.run()


if __name__ == "__main__":
    main()