from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .models import IntakeRequest, IntakeResult
from .parser import parse_offer
from .validator import validate_offer

BASE=Path(__file__).resolve().parent.parent
app=FastAPI(title="Elysian Offer Writer",version="0.1.0")
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
