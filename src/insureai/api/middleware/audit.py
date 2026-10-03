"""HTTP request audit: structured log line per request with request-id, user,
status and latency. DB-level audit of agent/human actions lives in
insureai.audit.trail - this covers the transport layer only."""
from __future__ import annotations

import logging
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("insureai.http")


class RequestAuditMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req_headers = MutableHeaders(scope=scope)
        request_id = req_headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        status = 0

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers.append("X-Request-ID", request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            dur_ms = (time.perf_counter() - start) * 1000
            user = scope.get("state", {}).get("user")
            logger.info(
                "rid=%s method=%s path=%s status=%s dur_ms=%.1f user=%s",
                request_id, scope["method"], scope["path"], status, dur_ms,
                getattr(user, "sub", None) or "-",
            )
