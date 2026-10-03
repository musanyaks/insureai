"""Shared DB access for agents (worker-side). Fresh connection per unit of work —
low volume in v1; a pool arrives when throughput demands it. clean_row() makes
DB rows JSON-safe for envelope payloads (dates -> ISO strings, Decimals -> float)."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row


@contextmanager
def get_conn(dsn: str):
    with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn


def clean_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {}
    out: dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, (date, datetime)):
            out[k] = v.isoformat()
        elif isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out