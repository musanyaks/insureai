"""Append-only audit. Every envelope crossing any agent gets one row.
Fail-soft on DB outage (log + continue) so auditing problems never take down
the fleet - but every failure is visible in logs."""
import logging

import psycopg
from psycopg.types.json import Jsonb

from insureai.schemas.envelope import AgentEnvelope

logger = logging.getLogger(__name__)


class AuditTrail:
    _INSERT = """
        INSERT INTO agent_messages
            (task_id, correlation_id, from_agent, to_agent, event, priority, payload, model_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    def __init__(self, dsn: str | None) -> None:
        self._dsn = dsn
        self._conn: psycopg.Connection | None = None

    def record(self, env: AgentEnvelope) -> None:
        if not self._dsn or not env.audit:
            return
        try:
            if self._conn is None or self._conn.closed:
                self._conn = psycopg.connect(self._dsn)
            with self._conn.cursor() as cur:
                cur.execute(self._INSERT, (
                    env.task_id, env.correlation_id, env.from_agent, env.to_agent,
                    env.event, env.priority.value, Jsonb(env.payload), env.model_version,
                ))
            self._conn.commit()
        except Exception:
            logger.warning("audit write failed - continuing without audit", exc_info=True)
            self._conn = None
