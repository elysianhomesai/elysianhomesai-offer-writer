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

    re_match = re.match(r"\s*\$?([\d,.]+)\s*(k)?\b",low)\n    x=re_match or m(r"(?:offer(?:ing)?|offer price|purchase price|price)\s*(?:of|is|:)?\s*\$?([\d,.]+)\s*(k)?\b")
    if x:
        value=_money(x.group(1),x.group(2))
        if value is not None:data.purchase_price=value
    x=m(r"\$?([\d,.]+)\s*(k)?\s*(?:deposit|emd|earnest)")
    if x:
        value=_money(x.group(1),x.group(2))
        if value is not None:data.deposit=value
    x=m(r"(\d+(?:\.\d+)?)\s*%\s*(?:down|down payment)")
    if x:data.down_payment_percent=float(x.group(1))
    for kind in ("conventional","fha","va","cash"):
        if m(rf"\b{kind}\b"): data.financing_type=kind;break
    if data.purchase_price and data.down_payment_percent is not None and data.financing_type!="cash":data.mortgage_amount=round(data.purchase_price*(1-data.down_payment_percent/100))

    x=m(r"(?:max(?:imum)?\s*)?(\d+(?:\.\d+)?)\s*%\s*(?:max\s*)?(?:interest|rate)")
    if not x:x=m(r"(?:interest|rate)\s*(?:not\s+to\s+exceed|max(?:imum)?)?\s*(\d+(?:\.\d+)?)\s*%")
    if x:data.interest_rate_cap=float(x.group(1))
    x=m(r"(\d+)\s*[- ]?year\s*(?:mortgage|loan|term)?")
    if x:data.mortgage_term_years=int(x.group(1))
    x=m(r"(?:commitment|mortgage commitment)(?:\s+(?:date|by))?\s*(20\d{2}-\d{2}-\d{2})")
    if x:data.mortgage_commitment_date=x.group(1)

    data.sale_transfer_contingency=_bool_phrase(low,r"(?:sale|sell).{0,20}(?:contingenc|buyer.?s property)",r"(?:no|without|waive).{0,15}(?:sale|sell).{0,20}(?:contingenc|buyer.?s property)")
    data.building_code_contingency=_bool_phrase(low,r"building code.{0,12}contingenc",r"(?:no|without|waive).{0,15}building code.{0,12}contingenc")

    if m(r"\b(no|waive|waiving|decline|declining)\s+(?:home\s+)?inspection"):data.inspection=False
    elif "inspection" in low:data.inspection=True
    x=m(r"inspection(?:s)?(?:\s+within|\s+in|\s*)?\s*(\d+)\s*(?:calendar\s*)?days?") or m(r"(\d+)\s*(?:calendar\s*)?days?\s+(?:for\s+)?inspection")
    if x:data.inspection_days=int(x.group(1))
    x=m(r"(?:inspection|inspections)\s*(\d+)\s*[\/-]\s*(\d+)\s*[\/-]\s*(\d+)")
    if x:
        data.inspection=True;data.inspection_days=int(x.group(1));data.inspection_second_period_days=int(x.group(2));data.inspection_third_period_days=int(x.group(3))
    data.radon_inspection=_bool_phrase(low,r"(?:radon\s+(?:yes|included|inspection|test)|with\s+radon)",r"(?:no|without|waive)\s+radon")

    x=m(r"\$?([\d,.]+)\s*(k)?\s*(?:seller\s+)?concession") or m(r"(?:seller\s+)?concession(?:s)?\s*(?:of|at|for)\s*\$?([\d,.]+)\s*(k)?")
    if x:
        value=_money(x.group(1),x.group(2))
        if value is not None:data.seller_concession=value
    x=m(r"escalat(?:e|ion).*?(?:by|increment)\s*\$?([\d,.]+)\s*(k)?.*?(?:to|cap(?:ped)?(?:\s+at)?)\s*\$?([\d,.]+)\s*(k)?")
    if x:
        increment=_money(x.group(1),x.group(2))
        cap=_money(x.group(3),x.group(4))
        if increment is not None and cap is not None:
            data.escalation=True
            data.escalation_increment=increment
            data.escalation_cap=cap

    x=m(r"(?:close|closing)\s+(?:on\s+)?(20\d{2}-\d{2}-\d{2})")
    if x:data.closing_date=x.group(1)
    x=m(r"(?:close|closing)\s+(?:on\s+20\d{2}-\d{2}-\d{2}\s+)?(?:in|at)\s+([a-z ]+?)\s+county") or m(r"([a-z]+)\s+county\s+(?:clerk|closing)")
    if x:data.closing_county=x.group(1).strip().title()
    if m(r"possession\s+(?:at|upon)\s+clos"):data.possession="at_closing"
    elif m(r"seller.{0,20}(?:retain|post.?clos).{0,20}possession"):data.possession="seller_retained"
    elif m(r"buyer.{0,20}(?:early|pre.?clos).{0,20}possession"):data.possession="buyer_early"

    data.systems_working_order=_bool_phrase(low,r"systems?.{0,20}working order",r"(?:no|not).{0,12}systems?.{0,20}working order")
    if m(r"property (?:condition )?disclosure.{0,12}(?:provided|received)"):data.property_disclosure_status="provided"
    elif m(r"property (?:condition )?disclosure.{0,12}exempt"):data.property_disclosure_status="exempt"
    if m(r"(?:primary|principal) residence"):data.hetpa_basis="primary_residence"
    elif m(r"lineal relation|spouse of seller"):data.hetpa_basis="lineal_relation_or_spouse"
    elif m(r"seller.{0,10}(?:estate|trust|business entity)"):data.hetpa_basis="seller_estate_trust_business"
    elif m(r"hetpa.{0,10}addendum"):data.hetpa_basis="addendum_required"

    if m(r"(?:elysian homes|broker).{0,20}(?:brought|broker)"):data.broker_brought_sale=True
    x=m(r"broker(?:age)?\s*(?:is|:)?\s*([a-z][a-z &.'-]{2,40})")
    if x:data.broker_name=x.group(1).strip().title()
    if "elysian homes" in low:data.broker_brought_sale=True;data.broker_name="Elysian Homes"\n    x=m(r"(?:agent|realtor)\\s+(?:name\\s+)?(?:is\\s+)?([a-z][a-z .-]{1,50}?)(?=\\.|,|;|\\s+with\\s+|\\s+at\\s+|$)")\n    if x:data.agent_name=x.group(1).strip().title()

    data.well_septic=bool(m(r"\b(well|septic)\b"))
    data.additional_personal_property=bool(m(r"additional personal property"))
    x=m(r"(?:offer\s+)?expir(?:e|es|ation)\s+(20\d{2}-\d{2}-\d{2})(?:\s+(?:at\s+)?(\d{1,2}:\d{2}))?")
    if x:data.offer_expiration=x.group(1)+("T"+x.group(2) if x.group(2) else "")
    return data
