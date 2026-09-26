from pathlib import Path
from io import BytesIO

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .models import IntakeRequest, IntakeResult, ClarificationRequest
from .parser import parse_offer
from .validator import validate_offer
from .generate_grar import generate_contract

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="Elysian Offer Writer", version="0.5.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/intake", response_model=IntakeResult)
def intake(req: IntakeRequest):
    offer = parse_offer(req.mls_number, req.buyers, req.offer_text)\n    offer.agent_name = req.agent_name.strip()
    offer.agent_license_no = req.agent_license_no
    offer.agent_phone = req.agent_phone
    offer.agent_cell = req.agent_cell
    offer.agent_email = req.agent_email
    if offer.buyers:
        offer.buyers[0].phone = req.buyer_phone
        offer.buyers[0].cell = req.buyer_cell
        offer.buyers[0].email = req.buyer_email
    checks, ready = validate_offer(offer)
    return IntakeResult(offer=offer, checks=checks, ready=ready)


@app.post("/api/clarify", response_model=IntakeResult)
def clarify(req: ClarificationRequest):
    offer = req.offer.model_copy(update=req.updates)
    if offer.purchase_price and offer.down_payment_percent is not None and offer.financing_type != "cash":
        offer.mortgage_amount = round(
            offer.purchase_price * (1 - offer.down_payment_percent / 100)
        )
    checks, ready = validate_offer(offer)
    return IntakeResult(offer=offer, checks=checks, ready=ready)


@app.post("/api/final-grar-pdf")
def final_grar_pdf(req: ClarificationRequest):
    payload = req.offer.model_dump()
    payload.update(req.updates)
    offer = type(req.offer).model_validate(payload)
    checks, ready = validate_offer(offer)
    if not ready:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail={"missing": [x.label for x in checks if x.status != "complete"]})
    pdf = generate_contract(offer)
    return StreamingResponse(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="GRAR-Offer-{offer.mls_number}.pdf"'})

@app.post("/api/contract-summary")
def contract_summary(req: ClarificationRequest):
    offer = req.offer.model_copy(update=req.updates)
    checks, ready = validate_offer(offer)
    if not ready:
        return {
            "error": "Offer is not complete",
            "missing": [x.label for x in checks if x.status != "complete"],
        }

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("ELYSIAN HOMES", styles["Title"]),
        Paragraph("Purchase Offer - Final Data Review", styles["Heading2"]),
        Paragraph(
            "This document is a completed offer-data review for agent verification. "
            "It is not the copyrighted GRAR/Monroe County Bar Association Purchase "
            "and Sale Contract and is not a substitute for generating the approved "
            "form in TransactionDesk.",
            styles["BodyText"],
        ),
        Spacer(1, 14),
    ]

    rows = []
    for check in checks:
        value = check.value
        if isinstance(value, bool):
            value = "Yes" if value else "No"
        rows.append(
            [
                check.section,
                check.label,
                str(value if value is not None else ""),
            ]
        )

    table = Table(rows, colWidths=[105, 190, 205])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            "Agent must verify all terms before transferring them to the approved "
            "contract form and sending for signature.",
            styles["BodyText"],
        )
    )
    doc.build(story)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="offer-{offer.mls_number}-final-review.pdf"'
            )
        },
    )
