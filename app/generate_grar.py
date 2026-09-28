from io import BytesIO
from pathlib import Path
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

BASE=Path(__file__).resolve().parent.parent
TEMPLATES=BASE/"templates"
MAIN=TEMPLATES/"Purchase Contract SFR 2026.pdf"
ESCALATION=TEMPLATES/"A36F8C13-66FC-45BC-A617-EFA2E642485C_20260926161053.pdf"
PERSONAL=TEMPLATES/"Additional Personal Property Agreement.pdf"
WELL=TEMPLATES/"Addendum Well and Spetic.pdf"
AGENCY=TEMPLATES/"Agency Disclosure.pdf"
FAIR_HOUSING=TEMPLATES/"Fair Housing & Discrimination Disclosure.pdf"

def money(v): return "" if v is None else f"{int(v):,}"
def date(v):
    if not v:return ""
    s=str(v).split("T")[0]
    try:return datetime.strptime(s,"%Y-%m-%d").strftime("%m/%d/%Y")
    except ValueError:return s
def txt(c,x,y,v,size=8,width=None):
    if v is None:return
    s=str(v)
    if width:
        while c.stringWidth(s,"Helvetica",size)>width and size>5:size-=.5
    c.setFont("Helvetica",size);c.drawString(x,792-y,s)
def check(c,x,y):c.setFont("Helvetica-Bold",10);c.drawString(x,792-y,"X")
def names(o):
    b=[x.name for x in o.buyers]+["","",""]
    return b[:4],[o.seller_1 or "",o.seller_2 or ""]

def overlay(n,o):
    b=BytesIO();c=canvas.Canvas(b,pagesize=letter);buyers,sellers=names(o)
    if n==1:
        txt(c,74,207,sellers[0],8,205);txt(c,308,207,sellers[1],8,205);txt(c,74,244,buyers[0],8,205);txt(c,305,244,buyers[1],8,205)
        txt(c,396,324,o.property_address,8,175);txt(c,140,342,o.county,8,135)
        if o.municipality_type:check(c,*{"Town":(283,342),"City":(324,342),"Village":(356,342)}[o.municipality_type])
        txt(c,410,342,o.municipality_name,8,128);txt(c,132,360,o.zip_code,8,55);txt(c,290,360,o.tax_number,7,280);txt(c,488,391,o.lot_size,7,85);txt(c,238,407,o.building_description,7,330)
        if o.systems_working_order:check(c,73,654)
        txt(c,266,707,o.excluded_items,7,300)
    elif n==2:
        txt(c,505,60,money(o.purchase_price),9,70);txt(c,505,94,money(o.deposit),9,70)
        if o.deposit_form:check(c,*{"cash":(285,85),"personal_check":(324,85),"official_bank_check":(410,85),"eft":(122,98),"wire":(246,98)}[o.deposit_form])
        if o.deposit_delivery=="delivered":check(c,118,112)
        elif o.deposit_delivery=="within_2_days":check(c,192,112)
        txt(c,136,125,o.escrow_agent,7,255);txt(c,103,136,o.escrow_bank,7,190)
        if o.seller_concession is not None:check(c,269,201);txt(c,284,202,money(o.seller_concession),8,90)
        if o.financing_type=="cash":check(c,73,619);txt(c,341,632,date(o.cash_proof_date),8,220)
        elif o.financing_type:
            check(c,73,472);txt(c,482,474,o.financing_type.title(),7,92)
            if o.down_payment_percent is not None:check(c,379,486);txt(c,399,487,100-float(o.down_payment_percent),8,45)
            txt(c,339,501,o.interest_rate_cap,8,45);txt(c,444,501,o.mortgage_term_years,8,22);txt(c,352,512,date(o.mortgage_commitment_date),8,78);txt(c,173,563,money(o.mortgage_repair_threshold),8,78)
        if o.sale_transfer_contingency:check(c,55,703)
    elif n==3:
        if o.building_code_contingency:check(c,55,51)
        if o.other_contingencies:check(c,55,137);txt(c,87,149,o.other_contingencies,7,475)
        if o.inspection is True:
            check(c,55,192);check(c,87,205)
            if o.radon_inspection:check(c,183,218)
            txt(c,407,220,o.other_inspections,7,105);txt(c,408,234,o.inspection_days,8,25);txt(c,433,255,o.inspection_second_period_days,8,25);txt(c,466,286,o.inspection_third_period_days,8,25)
        elif o.inspection is False:check(c,55,442)
        txt(c,519,468,o.attorney_approval_days,8,45)
        if o.systems_working_order:check(c,73,665)
    elif n==4:
        if o.property_disclosure_status=="provided":check(c,73,51)
        elif o.property_disclosure_status=="exempt":check(c,73,64)
        txt(c,157,98,money(o.co_cost_threshold),8,115);txt(c,451,133,o.zoning_use,7,120)
        if o.hetpa_basis:check(c,*{"primary_residence":(55,261),"lineal_relation_or_spouse":(55,285),"seller_estate_trust_business":(55,298),"addendum_required":(55,312)}[o.hetpa_basis])
        txt(c,307,425,o.closing_county,8,150);txt(c,233,435,date(o.closing_date),8,150)
        if o.possession=="at_closing":check(c,73,500)
        elif o.possession=="seller_retained":check(c,73,524)
        elif o.possession=="buyer_early":check(c,73,587)
    elif n==5:
        if o.broker_brought_sale:check(c,73,478);txt(c,192,479,o.broker_name,8,225)
        elif o.broker_brought_sale is False:check(c,73,491)
    elif n==6:
        if o.additional_personal_property:check(c,73,448)
        if o.escalation:check(c,248,474)
        if o.well_septic:check(c,428,488)
        txt(c,56,568,o.other_terms,7,515)
        if o.offer_expiration:
            parts=str(o.offer_expiration).split("T");txt(c,228,633,date(parts[0]),8,205)
            if len(parts)>1:
                hh,mm=map(int,parts[1][:5].split(":"));am=hh<12;txt(c,451,633,f"{hh%12 or 12}:{mm:02d}",8,65);check(c,510 if am else 545,632)
    elif n==8:
        # Buyer-side administrative information
        txt(c,118,72,o.property_address,8,310);txt(c,465,72,o.mls_number,8,105)
        txt(c,326,92,buyers[0],8,245);txt(c,326,113,buyers[1],8,245)
        if o.buyers:
            txt(c,326,175,o.buyers[0].phone or o.buyers[0].cell,8,120)
            txt(c,326,196,o.buyers[0].email,8,245)
        txt(c,326,239,o.buyer_attorney_name,8,245)
        txt(c,326,371,o.buyer_attorney_email,8,245)

        # Elysian Homes brokerage information is constant
        txt(c,326,392,"Elysian Homes by Mark Siwiec and Associates",6.5,245)
        txt(c,326,412,"10991239051",8,245)
        txt(c,326,440,"1357 Monroe Avenue",8,245)
        txt(c,326,461,"Rochester, NY 14618",8,245)
        txt(c,326,482,"585-330-8750",8,125)

        # Selling agent information varies by agent
        txt(c,326,524,o.agent_name,8,245)
        txt(c,326,545,o.agent_license_no,8,245)
        txt(c,326,586,o.agent_phone,8,125)
        txt(c,326,607,o.agent_cell,8,125)
        txt(c,326,628,o.agent_email,8,245)
    c.showPage();c.save();b.seek(0);return PdfReader(b).pages[0]

def addendum(kind,o):
    b=BytesIO();c=canvas.Canvas(b,pagesize=letter);buyers,sellers=names(o)
    if kind=="escalation":
        txt(c,80,170,sellers[0],8,205);txt(c,355,170,buyers[0],8,205);txt(c,80,195,sellers[1],8,205);txt(c,355,195,buyers[1],8,205);txt(c,95,220,o.property_address,8,450);txt(c,306,256,date(o.contract_date),8,70);txt(c,267,304,money(o.escalation_increment),8,55);txt(c,112,333,money(o.escalation_cap),8,100)
    elif kind=="personal":
        txt(c,80,177,sellers[0],8,205);txt(c,292,177,buyers[0],8,255);txt(c,80,205,sellers[1],8,205);txt(c,292,205,buyers[1],8,255);txt(c,82,233,o.property_address,8,315);txt(c,438,233,date(o.contract_date),8,115);txt(c,108,261,o.personal_property_sum_words,8,300);txt(c,468,261,money(o.personal_property_sum),8,80);txt(c,38,305,o.personal_property_description,8,530)
    elif kind=="well":
        txt(c,77,145,sellers[0],8,205);txt(c,328,145,buyers[0],8,240);txt(c,77,162,sellers[1],8,205);txt(c,328,162,buyers[1],8,240);txt(c,88,179,o.property_address,8,480)
        if o.well_potability:check(c,304,196)
        if o.well_volume:check(c,446,196)
        if o.septic_inspection:check(c,37,211)
        txt(c,384,213,o.well_septic_completion_days,8,25)
        if o.well_septic_expense=="buyer":check(c,84,225)
        elif o.well_septic_expense=="seller":check(c,140,225)
        txt(c,178,239,o.well_septic_objection_days,8,25);txt(c,160,263,o.well_septic_negotiation_days,8,25);txt(c,386,345,money(o.restoration_escrow),8,75);txt(c,352,356,o.restoration_days,8,25)
    c.showPage();c.save();b.seek(0);return PdfReader(b).pages[0]

def generate_contract(o):
    if not MAIN.exists():raise FileNotFoundError("Official GRAR template is not installed.")
    out=PdfWriter()
    for i,p in enumerate(PdfReader(str(MAIN)).pages,1):p.merge_page(overlay(i,o));out.add_page(p)
    # Standard package documents are always included.
    for standard in (AGENCY, FAIR_HOUSING):
        if standard.exists():
            for p in PdfReader(str(standard)).pages:out.add_page(p)
    for path,kind,on in [(ESCALATION,"escalation",o.escalation),(PERSONAL,"personal",o.additional_personal_property),(WELL,"well",o.well_septic)]:
        if on:
            p=PdfReader(str(path)).pages[0];p.merge_page(addendum(kind,o));out.add_page(p)
    b=BytesIO();out.write(b);b.seek(0);return b
