from .models import OfferData, FieldCheck

def validate_offer(o: OfferData) -> tuple[list[FieldCheck], bool]:
    checks=[]
    def add(key,label,value,required=True,reason=None,section="Offer Terms",input_type="text",options=None):
        missing=required and (value is None or value=="" or value==[])
        checks.append(FieldCheck(key=key,label=label,status="missing" if missing else "complete",value=value,
            reason=reason if missing else None,section=section,input_type=input_type,options=options or []))

    add("mls_number","MLS Number",o.mls_number,True,"Required to identify the property.","Property")
    add("property_address","Property Address",o.property_address,True,"Required on the purchase contract.","Property")
    add("county","County",o.county,True,"Required for the property description.","Property")
    add("municipality_type","Municipality Type",o.municipality_type,True,"Select Town, City, or Village.","Property","select",["Town","City","Village"])
    add("municipality_name","Municipality Name",o.municipality_name,True,"Enter the municipality shown for the property.","Property")
    add("zip_code","ZIP Code",o.zip_code,True,"Required for the property description.","Property")

    add("buyers","Buyer(s)",", ".join(b.name for b in o.buyers),True,"At least one buyer is required.","Price & Parties")
    add("purchase_price","Purchase Price",o.purchase_price,True,"Confirm the offered purchase price.","Price & Parties","money")
    add("deposit","Deposit",o.deposit,True,"Confirm the deposit amount.","Price & Parties","money")
    add("seller_concession","Seller Concession",o.seller_concession,False,section="Price & Parties")

    add("financing_type","Financing",o.financing_type,True,"Choose cash or financing type.","Financing","select",["conventional","fha","va","cash","other"])
    if o.financing_type and o.financing_type!="cash":
        add("down_payment_percent","Down Payment %",o.down_payment_percent,True,"Confirm down payment percentage.","Financing","number")
        add("mortgage_amount","Calculated Mortgage",o.mortgage_amount,True,"Calculated from price and down payment.","Financing","money")
        add("mortgage_commitment_date","Mortgage Commitment Date",o.mortgage_commitment_date,True,"Required when using a mortgage contingency.","Financing","date")
        add("interest_rate_cap","Maximum Interest Rate %",o.interest_rate_cap,True,"The mortgage contingency contains a maximum interest-rate field.","Financing","number")
        add("mortgage_term_years","Mortgage Term (Years)",o.mortgage_term_years,True,"The mortgage contingency contains a loan-term field.","Financing","number")

    add("sale_transfer_contingency","Sale/Transfer of Buyer's Property",o.sale_transfer_contingency,True,"Confirm whether this contingency applies.","Contingencies","boolean")
    add("building_code_contingency","Building Code Compliance Contingency",o.building_code_contingency,True,"Confirm whether this contingency applies.","Contingencies","boolean")

    add("inspection","Inspection Election",o.inspection,True,"Confirm inspection or inspection declined.","Inspections","boolean")
    if o.inspection is True:
        add("inspection_days","Inspection First Time Period",o.inspection_days,True,"Confirm the inspection completion period.","Inspections","number")
        add("inspection_second_period_days","Inspection Second Time Period",o.inspection_second_period_days,True,"Confirm the period for Buyer Objections after inspections.","Inspections","number")
        add("inspection_third_period_days","Inspection Third Time Period",o.inspection_third_period_days,True,"Confirm the negotiation period after Buyer Objections.","Inspections","number")
        add("radon_inspection","Radon Inspection",o.radon_inspection,True,"Confirm whether radon testing is included.","Inspections","boolean")

    add("attorney_approval_days","Attorney Approval Period",o.attorney_approval_days,True,"Contract defaults to 3 if left blank.","Attorney Approval","number")

    add("systems_working_order","Systems in Working Order at Closing",o.systems_working_order,True,"Confirm whether the optional working-order provision is selected.","Property Conditions","boolean")
    add("property_disclosure_status","Property Condition Disclosure",o.property_disclosure_status,True,"Confirm provided or exempt.","Property Conditions","select",["provided","exempt"])
    add("hetpa_basis","HETPA Representation",o.hetpa_basis,True,"At least one HETPA representation must be selected.","Property Conditions","select",["primary_residence","lineal_relation_or_spouse","seller_estate_trust_business","addendum_required"])

    add("closing_date","Closing Date",o.closing_date,True,"Confirm the proposed closing date.","Closing","date")
    add("closing_county","Closing County",o.closing_county,True,"The contract identifies the county clerk's office.","Closing")
    add("possession","Possession",o.possession,True,"Confirm when Buyer receives possession.","Closing","select",["at_closing","seller_retained","buyer_early"])

    add("broker_brought_sale","Broker Brought About Sale",o.broker_brought_sale,True,"Confirm the broker provision.","Broker & Addenda","boolean")
    if o.broker_brought_sale is True:
        add("broker_name","Broker Name",o.broker_name,True,"Enter the broker named in the contract.","Broker & Addenda")
        add("agent_name","Agent Name",o.agent_name,True,"Enter the agent preparing the offer.","Broker & Addenda")

    if o.escalation:
        add("escalation_increment","Escalation Increment",o.escalation_increment,True,"Required for the Price Escalation Agreement.","Addenda","money")
        add("escalation_cap","Escalation Cap",o.escalation_cap,True,"Required for the Price Escalation Agreement.","Addenda","money")

    add("offer_expiration","Offer Expiration",o.offer_expiration,True,"Confirm when the offer expires.","Life of Offer","datetime-local")

    missing=any(c.status!="complete" for c in checks)
    return checks, not missing
