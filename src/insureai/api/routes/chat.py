"""Natural language entry point. v1 uses a deterministic intent detector; when
the orchestrator lands (Phase 1), detect_intent is replaced by LLM
classification - the route contract (ChatRequest/ChatResponse) does not change,
which is exactly why it's a separate function."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from insureai.api.deps import AuditDep, BusDep, PoolDep
from insureai.api.middleware.auth import Role, require_roles
from insureai.api.services import start_investigation

router = APIRouter(prefix="/chat", tags=["chat"])

Viewer = require_roles(Role.VIEWER)

CLAIM_RE = re.compile(r"CLM-\d{4}-\d{6}", re.IGNORECASE)
ANALYTICS_KEYWORDS = ("loss ratio", "how many claims", "reserv", "premium",
                      "frequency", "severity", "portfolio")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    intent: str
    text: str
    investigation_id: str | None = None


def detect_intent(message: str) -> tuple[str, str | None]:
    """Returns (intent, entity). Swap point for LLM classification."""
    match = CLAIM_RE.search(message)
    if match:
        return "investigate_claim", match.group(0).upper()
    lowered = message.lower()
    if any(k in lowered for k in ANALYTICS_KEYWORDS):
        return "analytics_question", None
    return "unknown", None


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, pool: PoolDep, bus: BusDep, audit: AuditDep,
         user=Depends(Viewer)):
    intent, entity = detect_intent(body.message)

    if intent == "investigate_claim":
        result = start_investigation(
            pool, bus, audit, claim_id=entity,
            trigger="chat", requested_by=getattr(user, "sub", None),
        )
        if result is None:
            return ChatResponse(
                intent=intent,
                text=f"Claim {entity} was not found. Check the ID and try again.",
            )
        if result["already_running"]:
            return ChatResponse(
                intent=intent,
                text=(f"Claim {entity} is already under investigation "
                      f"({result['investigation_id']})."),
                investigation_id=result["investigation_id"],
            )
        return ChatResponse(
            intent=intent,
            text=(f"Started investigation {result['investigation_id']} for claim "
                  f"{entity} at priority {result['priority']}. Agents have been "
                  f"notified; the report will appear when they complete."),
            investigation_id=result["investigation_id"],
        )

    if intent == "analytics_question":
        return ChatResponse(
            intent=intent,
            text=("Numeric analytics are answered by the deterministic SQL agent "
                  "(Phase 1) - scores and figures never come from generated text. "
                  "Until then, use GET /claims and GET /investigations."),
        )

    return ChatResponse(
        intent="unknown",
        text=("I can start a claim investigation - mention a claim ID like "
              "CLM-2026-000100. Analytics queries arrive with the SQL agent."),
    )
