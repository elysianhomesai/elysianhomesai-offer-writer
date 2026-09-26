from typing import Literal
from pydantic import BaseModel, Field

Status = Literal["complete", "missing", "needs_confirmation"]

class Buyer(BaseModel):
    name: str

class OfferData(BaseModel):
    mls_number: str
    buyers: list[Buyer]
    raw_offer_text: str

    # Property / Paragraph 1
    property_address: str | None = None
    county: str | None = None
    municipality_type: Literal["Town","City","Village"] | None = None
    municipality_name: str | None = None
    zip_code: str | None = None
    tax_number: str | None = None
    included_personal_property: str | None = None
    excluded_items: str | None = None

    # Price / Paragraph 2
    purchase_price: int | None = None
    deposit: int | None = None
    seller_concession: int | None = None
    seller_concession_type: Literal["dollars","percent"] = "dollars"

    # Contingencies / Paragraph 3
    financing_type: Literal["conventional","fha","va","cash","other"] | None = None
    down_payment_percent: float | None = None
    mortgage_amount: int | None = None
    mortgage_commitment_date: str | None = None
    interest_rate_cap: float | None = None
    mortgage_term_years: int | None = None
    sale_transfer_contingency: bool | None = None
    building_code_contingency: bool | None = None
    other_contingencies: str | None = None

    # Inspection / Paragraph 4
    inspection: bool | None = None
    inspection_days: int | None = None
    inspection_second_period_days: int | None = None
    inspection_third_period_days: int | None = None
    radon_inspection: bool | None = None
    other_inspections: str | None = None

    # Attorney / Paragraph 5
    attorney_approval_days: int = 3

    # Property information / Paragraphs 6-7
    systems_working_order: bool | None = None
    property_disclosure_status: Literal["provided","exempt"] | None = None
    hetpa_basis: Literal["primary_residence","lineal_relation_or_spouse","seller_estate_trust_business","addendum_required"] | None = None

    # Closing / Paragraph 8
    closing_date: str | None = None
    closing_county: str | None = None
    possession: Literal["at_closing","seller_retained","buyer_early"] | None = None

    # Broker / Paragraph 10
    broker_brought_sale: bool | None = None
    broker_name: str | None = None

    # Addenda / Paragraphs 10-11
    escalation: bool = False
    escalation_increment: int | None = None
    escalation_cap: int | None = None
    well_septic: bool = False
    additional_personal_property: bool = False
    other_terms: str | None = None

    # Life of offer / Paragraph 12
    offer_expiration: str | None = None
    notes: list[str] = Field(default_factory=list)

class IntakeRequest(BaseModel):
    mls_number: str
    buyers: str
    offer_text: str

class ClarificationRequest(BaseModel):
    offer: OfferData
    updates: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

class FieldCheck(BaseModel):
    key: str
    label: str
    status: Status
    value: str | int | float | bool | None = None
    reason: str | None = None
    section: str = "Offer Terms"
    input_type: str = "text"
    options: list[str] = Field(default_factory=list)

class IntakeResult(BaseModel):
    offer: OfferData
    checks: list[FieldCheck]
    ready: bool
