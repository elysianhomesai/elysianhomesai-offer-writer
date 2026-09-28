import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import httpx
from .models import OfferData
from .parser import parse_offer

SYSTEM = """You extract residential real-estate purchase-offer terms into structured JSON.
Read the agent's message semantically, not by exact keywords. Understand shorthand, paraphrases, casual language, numerals, relative dates, and common real-estate abbreviations.
Capture every fact actually stated or unambiguously implied. Never invent a material contract term.
Normalize dates to YYYY-MM-DD, datetimes to YYYY-MM-DDTHH:MM, and money to integer dollars.
Explicit waiver/decline language overrides generic mentions. Cash must not create mortgage terms.
Escalation requires escalation=true plus increment and cap when stated.
Return only one JSON object matching the supplied schema."""

def _merge(base: OfferData, values: dict) -> OfferData:
    payload=base.model_dump()
    for k,v in values.items():
        if k in payload and v is not None:
            payload[k]=v
    return OfferData.model_validate(payload)

def extract_offer(mls_number: str, buyers: str, text: str) -> OfferData:
    base=parse_offer(mls_number,buyers,text)
    key=os.getenv("ANTHROPIC_API_KEY")
    model=os.getenv("ANTHROPIC_MODEL")
    if not key or not model:
        base.notes.append("Semantic AI extraction unavailable: configure ANTHROPIC_API_KEY and ANTHROPIC_MODEL.")
        return base
    today=datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    user=f"""Today in Rochester, New York is {today}.
MLS number: {mls_number}
Buyer names supplied separately: {buyers}
Agent's natural-language offer message:
{text}

Extract the message into this JSON schema:
{json.dumps(OfferData.model_json_schema())}"""
    try:
        r=httpx.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":model,"max_tokens":4000,"temperature":0,"system":SYSTEM,
                  "messages":[{"role":"user","content":user}]},timeout=45.0)
        r.raise_for_status()
        raw=r.json()["content"][0]["text"].strip()
        if raw.startswith("```"):
            raw=raw.split("\n",1)[1].rsplit("```",1)[0]
        values=json.loads(raw)
        values["mls_number"]=mls_number.strip()
        values["raw_offer_text"]=text.strip()
        values.pop("buyers",None)
        return _merge(base,values)
    except Exception as e:
        base.notes.append(f"Semantic extraction fallback used: {type(e).__name__}")
        return base
