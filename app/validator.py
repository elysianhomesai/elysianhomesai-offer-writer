from .models import OfferData, FieldCheck

def validate_offer(o: OfferData) -> tuple[list[FieldCheck], bool]:
    checks=[]
    def add(key,label,value,required=True,reason=None):
        missing=required and (value is None or value=="" or value==[])
        checks.append(FieldCheck(key=key,label=label,status="missing" if missing else "complete",value=value,reason=reason if missing else None))

    add("mls_number","MLS Number",o.mls_number,True,"Required to identify the property.")
    add("buyers","Buyer(s)",", ".join(b.name for b in o.buyers),True,"At least one buyer is required.")
    add("purchase_price","Purchase Price",o.purchase_price,True,"Confirm the offered purchase price.")
    add("deposit","Deposit",o.deposit,True,"Confirm the deposit amount.")
    add("financing_type","Financing",o.financing_type,True,"Choose cash or financing type.")
    if o.financing_type and o.financing_type!="cash":
        add("down_payment_percent","Down Payment %",o.down_payment_percent,True,"Confirm down payment percentage.")
        add("mortgage_amount","Calculated Mortgage",o.mortgage_amount,True,"Calculated after price and down payment are known.")
        add("mortgage_commitment_date","Mortgage Commitment Date",o.mortgage_commitment_date,True,"Required when using a mortgage contingency.")
    add("inspection","Inspection Election",o.inspection,True,"Confirm inspection or inspection declined.")
    if o.inspection is True:
        add("inspection_days","Inspection First Time Period",o.inspection_days,True,"Confirm the inspection time period.")
    add("closing_date","Closing Date",o.closing_date,True,"Confirm the proposed closing date.")
    add("offer_expiration","Offer Expiration",o.offer_expiration,True,"Confirm when the offer expires.")
    if o.escalation:
        add("escalation_increment","Escalation Increment",o.escalation_increment,True,"Required for an escalation agreement.")
        add("escalation_cap","Escalation Cap",o.escalation_cap,True,"Required for an escalation agreement.")
    missing=any(c.status!="complete" for c in checks)
    return checks, not missing
