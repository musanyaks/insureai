from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class ClaimStatus(str, Enum):
    INTAKE = "INTAKE"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"


class Claim(BaseModel):
    claim_id: str
    policy_id: str
    loss_date: date
    reported_date: date
    claim_amount: Decimal
    repair_estimate: Decimal | None = None
    book_value_cost: Decimal | None = None
    garage_id: str | None = None
    accident_county: str
    loss_description: str | None = None
    theft_flag: bool = False
    nights_weekend: bool = False
    status: ClaimStatus = ClaimStatus.INTAKE
    created_at: datetime | None = None


class ClaimCreate(BaseModel):
    """Intake payload for POST /claims. claim_id and status are server-assigned."""
    policy_id: str
    loss_date: date
    reported_date: date
    claim_amount: Decimal
    repair_estimate: Decimal | None = None
    book_value_cost: Decimal | None = None
    garage_id: str | None = None
    accident_county: str
    loss_description: str | None = None
    theft_flag: bool = False
    nights_weekend: bool = False
