from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from .models import IntakeRequest, IntakeResult, ClarificationRequest
from .parser import parse_offer
from .validator import validate_offer\nfrom io import BytesIO\nfrom reportlab.lib.pagesizes import letter\nfrom reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle\nfrom reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle\nfrom reportlab.lib import colors

BASE=Path(__file__).resolve().parent.parent
app=FastAPI(title="Elysian Offer Writer",version="0.2.0")
app.mount("/static",StaticFiles(directory=BASE/"static"),name="static")

@app.get("/")
def home():
    return FileResponse(BASE/"static"/"index.html")

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/api/intake",response_model=IntakeResult)
def intake(req:IntakeRequest):
    offer=parse_offer(req.mls_number,req.buyers,req.offer_text)
    checks,ready=validate_offer(offer)
    return IntakeResult(offer=offer,checks=checks,ready=ready)

@app.post("/api/clarify",response_model=IntakeResult)
def clarify(req:ClarificationRequest):
    offer=req.offer.model_copy(update=req.updates)
    if offer.purchase_price and offer.down_payment_percent is not None and offer.financing_type != "cash":
        offer.mortgage_amount=round(offer.purchase_price*(1-offer.down_payment_percent/100))
    checks,ready=validate_offer(offer)
    return IntakeResult(offer=offer,checks=checks,ready=ready)


@app.post("/api/contract-summary")
def contract_summary(req:ClarificationRequest):
    offer=req.offer.model_copy(update=req.updates)
    checks,ready=validate_offer(offer)
    if not ready:
        return {"error":"Offer is not complete","missing":[x.label for x in checks if x.status!="complete"]}
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=letter,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42)
    styles=getSampleStyleSheet()
    story=[Paragraph("ELYSIAN HOMES",styles["Title"]),Paragraph("Purchase Offer — Final Data Review",styles["Heading2"]),
           Paragraph("This document is a completed offer-data review for agent verification. It is not the copyrighted GRAR/Monroe County Bar Association Purchase and Sale Contract and is not a substitute for generating the approved form in TransactionDesk.",styles["BodyText"]),Spacer(1,14)]
    rows=[]
    for ch in checks:
        val=ch.value
        if isinstance(val,bool): val="Yes" if val else "No"
        rows.append([ch.section,ch.label,str(val if val is not None else "")])
    t=Table(rows,colWidths=[105,190,205],repeatRows=0)
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.35,colors.lightgrey),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),8),("BACKGROUND",(0,0),(0,-1),colors.whitesmoke)]))
    story.append(t);story.append(Spacer(1,14));story.append(Paragraph("Agent must verify all terms before transferring them to the approved contract form and sending for signature.",styles["BodyText"]))
    doc.build(story);buf.seek(0)
    return StreamingResponse(buf,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="offer-{offer.mls_number}-final-review.pdf"'})
