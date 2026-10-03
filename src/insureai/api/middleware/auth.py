"""JWT auth. Pure ASGI middleware: parses the bearer token, attaches a User to
scope.state, rejects invalid tokens with 401. Enforcement happens in route
dependencies (require_roles), so GET/POST can demand different clearance.

Token hierarchy: viewer(0) < officer(1) < admin(2). An officer satisfies any
viewer-level requirement; admin satisfies everything. Swap-in point for
Keycloak/OIDC later - the middleware shape doesn't change."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum

import jwt
from fastapi import HTTPException
from pydantic import BaseModel
from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class Role(str, Enum):
    VIEWER = "viewer"
    OFFICER = "officer"
    ADMIN = "admin"


_LEVEL = {Role.VIEWER: 0, Role.OFFICER: 1, Role.ADMIN: 2}


class User(BaseModel):
    sub: str
    roles: list[Role] = []

    @property
    def clearance(self) -> int:
        return max((_LEVEL[r] for r in self.roles), default=-1)


class AuthMiddleware:
    def __init__(self, app: ASGIApp, secret: str) -> None:
        self.app = app
        self.secret = secret

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)
        raw = headers.get("Authorization", "")
        token = raw.removeprefix("Bearer ").strip()

        if token:
            try:
                payload = jwt.decode(token, self.secret, algorithms=["HS256"])
                roles = [Role(r) for r in payload.get("roles", []) if r in Role._value2member_map_]
                user = User(sub=str(payload["sub"]), roles=roles)
            except (jwt.PyJWTError, KeyError):
                resp = JSONResponse({"detail": "invalid or expired token"}, status_code=401)
                await resp(scope, receive, send)
                return
            if "state" not in scope:
                scope["state"] = {}
            scope["state"]["user"] = user

        await self.app(scope, receive, send)


def mint_token(sub: str, roles: list[Role], secret: str, hours: int = 12) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": sub, "roles": [r.value for r in roles], "iat": now,
         "exp": now + timedelta(hours=hours)},
        secret, algorithm="HS256",
    )


def current_user(request: Request) -> User | None:
    return getattr(request.state, "user", None)


def require_roles(minimum: Role):
    """Route dependency: 401 if anonymous, 403 if clearance too low."""
    def dependency(request: Request) -> User:
        user = current_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="authentication required")
        if user.clearance < _LEVEL[minimum]:
            raise HTTPException(
                status_code=403,
                detail=f"requires role '{minimum.value}' or higher",
            )
        return user
    return dependency
