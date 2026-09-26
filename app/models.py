from typing import Literal
from pydantic import BaseModel, Field
Status = Literal["complete","missing","needs_confirmation"]
class Buyer(BaseModel):
    name: str
    phone: str|None=None
    cell: str|None=None
    email: str|None=None
class OfferData(BaseModel):
    mls_number:str; buyers:list[Buyer]; raw_offer_text:str
    seller_1:str|None=None; seller_2:str|None=None
    property_address:str|None=None; county:str|None=None; municipality_type:Literal["Town","City","Village"]|None=None; municipality_name:str|None=None; zip_code:str|None=None; tax_number:str|None=None; lot_size:str|None=None; building_description:str|None=None; excluded_items:str|None=None
    purchase_price:int|None=None; deposit:int|None=None; deposit_form:Literal["cash","personal_check","official_bank_check","eft","wire"]|None=None; deposit_delivery:Literal["delivered","within_2_days"]|None=None; escrow_agent:str|None=None; escrow_bank:str|None=None; seller_concession:float|None=None; seller_concession_type:Literal["dollars","percent"]="dollars"
    financing_type:Literal["conventional","fha","va","cash","other"]|None=None; down_payment_percent:float|None=None; mortgage_amount:int|None=None; mortgage_commitment_date:str|None=None; interest_rate_cap:float|None=None; mortgage_term_years:int|None=None; mortgage_repair_threshold:int|None=None; cash_proof_date:str|None=None; sale_transfer_contingency:bool|None=None; building_code_contingency:bool|None=None; other_contingencies:str|None=None
    inspection:bool|None=None; inspection_days:int|None=None; inspection_second_period_days:int|None=None; inspection_third_period_days:int|None=None; radon_inspection:bool|None=None; other_inspections:str|None=None
    attorney_approval_days:int=3; systems_working_order:bool|None=None; property_disclosure_status:Literal["provided","exempt"]|None=None; co_cost_threshold:int|None=0; zoning_use:str|None=None; hetpa_basis:Literal["primary_residence","lineal_relation_or_spouse","seller_estate_trust_business","addendum_required"]|None=None
    closing_date:str|None=None; closing_county:str|None=None; possession:Literal["at_closing","seller_retained","buyer_early"]|None=None
    broker_brought_sale:bool|None=None; broker_name:str|None=None; agent_name:str|None=None; agent_license_no:str|None=None; agent_phone:str|None=None; agent_cell:str|None=None; agent_email:str|None=None
    buyer_attorney_name:str|None=None; buyer_attorney_email:str|None=None; buyer_attorney_name:str|None=None; buyer_attorney_email:str|None=None
    escalation:bool=False; escalation_increment:int|None=None; escalation_cap:int|None=None
    well_septic:bool=False; well_potability:bool=False; well_volume:bool=False; septic_inspection:bool=False; well_septic_completion_days:int|None=None; well_septic_expense:Literal["buyer","seller"]|None=None; well_septic_objection_days:int|None=None; well_septic_negotiation_days:int|None=None; restoration_escrow:int|None=None; restoration_days:int|None=None
    additional_personal_property:bool=False; personal_property_sum:int|None=None; personal_property_sum_words:str|None=None; personal_property_description:str|None=None
    other_terms:str|None=None; contract_date:str|None=None; offer_expiration:str|None=None; notes:list[str]=Field(default_factory=list)
class IntakeRequest(BaseModel):
    mls_number:str; buyers:str; agent_name:str; offer_text:str
    buyer_phone:str|None=None; buyer_cell:str|None=None; buyer_email:str|None=None
    agent_license_no:str|None=None; agent_phone:str|None=None; agent_cell:str|None=None; agent_email:str|None=None
    buyer_attorney_name:str|None=None; buyer_attorney_email:str|None=None
class ClarificationRequest(BaseModel): offer:OfferData; updates:dict[str,str|int|float|bool|None]=Field(default_factory=dict)
class FieldCheck(BaseModel):
    key:str; label:str; status:Status; value:str|int|float|bool|None=None; reason:str|None=None; section:str="Offer Terms"; input_type:str="text"; options:list[str]=Field(default_factory=list)
class IntakeResult(BaseModel): offer:OfferData; checks:list[FieldCheck]; ready:bool
