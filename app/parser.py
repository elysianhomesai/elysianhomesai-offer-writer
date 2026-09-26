import re
from datetime import datetime
from .models import OfferData, Buyer

def _money(token: str | None, k: str | None = None) -> int | None:
    if token is None:
        return None
    cleaned = token.replace(",", "").replace("$", "").strip()
    if not cleaned or not re.fullmatch(r"\d+(?:\.\d+)?", cleaned):
        return None
    n = float(cleaned)
    return int(n * 1000 if k else n)

def _bool_phrase(low, yes, no):
    if re.search(no,low): return False
    if re.search(yes,low): return True
    return None

def parse_offer(mls_number: str, buyers: str, text: str) -> OfferData:
    low=text.lower()
    data=OfferData(mls_number=mls_number.strip(),buyers=[Buyer(name=x.strip()) for x in re.split(r",|\band\b",buyers) if x.strip()],raw_offer_text=text.strip())
    def m(pattern): return re.search(pattern,low)

    x=re.match(r"\s*\$?([\d,.]+)\s*(k)?\b",low) or m(r"(?:offer(?:ing)?|offer price|purchase price|price)\s*(?:of|is|:)?\s*\$?([\d,.]+)\s*(k)?\b")
    if x:data.purchase_price=_money(x.group(1),x.group(2))
    x=m(r"\$?([\d,.]+)\s*(k)?\s*(?:deposit|emd|earnest)")
    if x:data.deposit=_money(x.group(1),x.group(2))

    # Property/party facts supplied in natural language
    x=m(r"(?:for|property(?:\s+address)?(?:\s+is)?|located at)\s+(\d+\s+[^,.]+?)(?=,\s*[a-z .'-]+,\s*new york|,\s*[a-z .'-]+\s+new york)")
    if x:data.property_address=x.group(1).strip().title()
    x=m(r",\s*([a-z .'-]+),\s*new york\s+(\d{5})")
    if x:
        data.municipality_name=x.group(1).strip().title();data.zip_code=x.group(2)
    x=m(r"(?:in|,\s*)([a-z .'-]+)\s+county\b")
    if x:data.county=x.group(1).strip().title()
    x=m(r"\b(town|city|village)\s+of\s+([a-z .'-]+)")
    if x:
        data.municipality_type=x.group(1).title();data.municipality_name=x.group(2).strip().title()
    elif data.municipality_name:
        data.municipality_type="Town"

    for kind in ("conventional","fha","va","cash"):
        if m(rf"\b{kind}\b"):data.financing_type=kind;break
    x=m(r"(\d+(?:\.\d+)?)\s*%\s*(?:down|down payment)")
    if x:data.down_payment_percent=float(x.group(1))
    if data.purchase_price and data.down_payment_percent is not None and data.financing_type!="cash":
        data.mortgage_amount=round(data.purchase_price*(1-data.down_payment_percent/100))
    x=m(r"(?:commitment|mortgage commitment)(?:\s+(?:date|by))?\s*(20\d{2}-\d{2}-\d{2})")
    if x:data.mortgage_commitment_date=x.group(1)
    x=m(r"(?:proof of funds|proof that buyer has|proof of cash)(?:\s+(?:by|on))?\s*(20\d{2}-\d{2}-\d{2})")
    if x:data.cash_proof_date=x.group(1)

    # Deposit details
    if m(r"deposit.{0,40}\bwire transfer\b|\bdeposit by wire transfer\b"):data.deposit_form="wire"
    elif m(r"deposit.{0,40}\belectronic funds transfer\b|\bdeposit by eft\b"):data.deposit_form="eft"
    elif m(r"deposit.{0,40}\bofficial bank check\b"):data.deposit_form="official_bank_check"
    elif m(r"deposit.{0,40}\bpersonal check\b"):data.deposit_form="personal_check"
    elif m(r"deposit.{0,40}\bcash\b"):data.deposit_form="cash"
    if m(r"deposit.{0,80}(?:within\s+(?:two|2)\s+(?:calendar\s+)?days|within two calendar days)"):data.deposit_delivery="within_2_days"
    elif m(r"deposit.{0,40}(?:has been|is|was)?\s*delivered"):data.deposit_delivery="delivered"
    x=m(r"(?:held in escrow by|escrow(?: agent)?(?: is|:)?)[ ]+([a-z0-9 &.'-]+?)(?=,|\s+(?:to be )?deposited|\s+at\s+|\.)")
    if x:data.escrow_agent=x.group(1).strip().title()
    x=m(r"(?:deposited at|escrow bank(?: is|:)?|bank(?: is|:)?)[ ]+([a-z0-9 &.'-]+?)(?=\.|,|$)")
    if x:data.escrow_bank=x.group(1).strip().upper()

    data.sale_transfer_contingency=_bool_phrase(low,r"(?:sale|sell).{0,20}(?:contingenc|buyer.?s property)",r"(?:no|without|waive).{0,25}(?:sale|sell).{0,30}(?:contingenc|buyer.?s property)")
    data.building_code_contingency=_bool_phrase(low,r"building code.{0,20}contingenc",r"(?:no|without|waive).{0,25}building code.{0,20}contingenc")

    # Explicit decline controls the entire inspection election, including radon.
    declined=bool(m(r"\b(?:no|waive|waiving|waived|decline|declines|declined|declining)\s+(?:(?:all|any)\s+)?(?:(?:home|property)\s+)?inspections?\b"))
    if declined:
        data.inspection=False;data.radon_inspection=False
    else:
        if "inspection" in low:data.inspection=True
        x=m(r"(?:inspection|inspections)\s*(\d+)\s*[\/-]\s*(\d+)\s*[\/-]\s*(\d+)")
        if x:
            data.inspection_days=int(x.group(1));data.inspection_second_period_days=int(x.group(2));data.inspection_third_period_days=int(x.group(3))
        data.radon_inspection=_bool_phrase(low,r"(?:radon\s+(?:yes|included|inspection|test)|with\s+radon)",r"(?:no|without|waive|decline|declines|declined).{0,15}radon|radon.{0,15}(?:declined|waived)")

    if m(r"\bno seller concession\b|\bwithout seller concession\b"):data.seller_concession=0
    else:
        x=m(r"\$?([\d,.]+)\s*(k)?\s*(?:seller\s+)?concession") or m(r"(?:seller\s+)?concession(?:s)?\s*(?:of|at|for)\s*\$?([\d,.]+)\s*(k)?")
        if x:data.seller_concession=_money(x.group(1),x.group(2))

    # Escalation: find increment and cap independently so natural prose works.
    if "escalat" in low and not m(r"\bno\s+escalation\b"):
        inc=m(r"escalat(?:e|ion).*?\bby\s*\$?([\d,.]+)\s*(k)?")
        cap=m(r"(?:up\s+to|maximum(?:\s+purchase\s+price)?(?:\s+of)?|cap(?:ped)?(?:\s+at)?)\s*\$?([\d,.]+)\s*(k)?")
        if inc and cap:
            data.escalation=True;data.escalation_increment=_money(inc.group(1),inc.group(2));data.escalation_cap=_money(cap.group(1),cap.group(2))

    x=m(r"(?:close|closing)(?:\s+will\s+be)?\s+(?:on\s+)?(20\d{2}-\d{2}-\d{2})")
    if x:data.closing_date=x.group(1)
    x=m(r"(?:close|closing).{0,35}\bin\s+([a-z .'-]+?)\s+county")
    if x:data.closing_county=x.group(1).strip().title()
    if m(r"possession\s+(?:at|upon)\s+clos"):data.possession="at_closing"

    data.systems_working_order=_bool_phrase(low,r"systems?.{0,30}working order",r"(?:no|not).{0,15}systems?.{0,30}working order")
    if m(r"property condition disclosure(?: statement)?.{0,25}(?:has been |was |is )?(?:provided|received)"):data.property_disclosure_status="provided"
    elif m(r"property condition disclosure(?: statement)?.{0,25}exempt"):data.property_disclosure_status="exempt"
    if m(r"(?:primary|principal) residence"):data.hetpa_basis="primary_residence"
    x=m(r"(?:property is zoned|zoned)(?:\s+for|\s+as)?\s+([a-z0-9 /&.'-]+?)(?=\.|,|$)")
    if x:data.zoning_use=x.group(1).strip().title()

    if "elysian homes" in low:data.broker_brought_sale=True;data.broker_name="Elysian Homes"

    data.well_septic=bool(m(r"\b(well|septic)\b"))
    data.additional_personal_property=bool(m(r"additional personal property"))
    x=m(r"(?:offer\s+)?expir(?:e|es|ation)\s+(20\d{2}-\d{2}-\d{2})(?:\s+(?:at\s+)?(\d{1,2}:\d{2}))?")
    if x:data.offer_expiration=x.group(1)+("T"+x.group(2) if x.group(2) else "")
    return data
