import re
from .models import OfferData, Buyer

def _money(token: str, k: str | None) -> int:
    cleaned = token.replace(",", "").strip()
    if not cleaned:
        raise ValueError("Money value was empty")
    n = float(cleaned)
    return int(n * 1000 if k else n)

def parse_offer(mls_number: str, buyers: str, text: str) -> OfferData:
    low=text.lower()
    data=OfferData(
        mls_number=mls_number.strip(),
        buyers=[Buyer(name=x.strip()) for x in re.split(r",|\band\b", buyers) if x.strip()],
        raw_offer_text=text.strip(),
    )
    m=re.search(r"(?:offer(?:ing)?|price|at)\s*\$?([\d,.]+)\s*(k)?", low)
    if not m:
        m=re.match(r"\s*\$?([\d,.]+)\s*(k)?\b", low)
    if m: data.purchase_price=_money(m.group(1),m.group(2))

    m=re.search(r"\$?([\d,.]+)\s*(k)?\s*(?:deposit|emd|earnest)", low)
    if m: data.deposit=_money(m.group(1),m.group(2))

    m=re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:down|down payment)", low)
    if m: data.down_payment_percent=float(m.group(1))

    for kind in ("conventional","fha","va","cash"):
        if re.search(rf"\b{kind}\b", low):
            data.financing_type=kind
            break

    if data.purchase_price and data.down_payment_percent is not None and data.financing_type!="cash":
        data.mortgage_amount=round(data.purchase_price*(1-data.down_payment_percent/100))

    if re.search(r"\b(no|waive|waiving|decline|declining)\s+(?:home\s+)?inspection", low):
        data.inspection=False
    elif "inspection" in low:
        data.inspection=True
        m=re.search(r"inspection(?:s)?(?:\s+within|\s+in|\s*)?\s*(\d+)\s*(?:calendar\s*)?days?", low)
        if not m: m=re.search(r"(\d+)\s*(?:calendar\s*)?days?\s+(?:for\s+)?inspection", low)
        if m: data.inspection_days=int(m.group(1))

    # Prefer amount-before-label form (e.g. "$5k seller concession").
    # The optional words in the label-first pattern previously allowed the
    # amount capture to become empty on text such as "$5k seller concession".
    m=re.search(r"\$?([\d,.]+)\s*(k)?\s*(?:seller\s+)?concession(?:s)?\b", low)
    if not m:
        m=re.search(r"(?:seller\s+)?concession(?:s)?\s*(?:of|at|for)\s*\$?([\d,.]+)\s*(k)?\b", low)
    if m:
        data.seller_concession=_money(m.group(1),m.group(2))

    m=re.search(r"escalat(?:e|ion).*?(?:by|increment)\s*\$?([\d,.]+)\s*(k)?.*?(?:to|cap(?:ped)?(?:\s+at)?)\s*\$?([\d,.]+)\s*(k)?", low)
    if m:
        data.escalation=True
        data.escalation_increment=_money(m.group(1),m.group(2))
        data.escalation_cap=_money(m.group(3),m.group(4))

    data.well_septic=bool(re.search(r"\b(well|septic)\b",low))
    m=re.search(r"(?:close|closing)\s+(?:on\s+)?(20\d{2}-\d{2}-\d{2})", low)
    if m: data.closing_date=m.group(1)
    return data
