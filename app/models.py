from typing import Literal
from pydantic import BaseModel, Field

Status = Literal["complete", "missing", "needs_confirmation"]

class Buyer(BaseModel):
    name: str

class OfferData(BaseModel):
    mls_number: str
    buyers: list[Buyer]
    raw_offer_text: str
    purchase_price: int | None = None
    deposit: int | None = None
    seller_concession: int | None = None
    financing_type: Literal["conventional","fha","va","cash","other"] | None = None
    down_payment_percent: float | None = None
    mortgage_amount: int | None = None
    mortgage_commitment_date: str | None = None
    inspection: bool | None = None
    inspection_days: int | None = None
    closing_date: str | None = None
    offer_expiration: str | None = None
    escalation: bool = False
    escalation_increment: int | None = None
    escalation_cap: int | None = None
    well_septic: bool = False
    seller_concession_type: Literal["dollars","percent"] = "dollars"
    notes: list[str] = Field(default_factory=list)

class IntakeRequest(BaseModel):
    mls_number: str
    buyers: str
    offer_text: str

class FieldCheck(BaseModel):
    key: str
    label: str
    status: Status
    value: str | int | float | bool | None = None
    reason: str | None = None

class IntakeResult(BaseModel):
    offer: OfferData
    checks: list[FieldCheck]
    ready: bool
