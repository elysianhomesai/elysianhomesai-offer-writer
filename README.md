# Elysian Homes AI Offer Writer

V1 is an intake and validation prototype for Elysian Homes agents. It does not create contracts or send data to TransactionDesk.

## Current flow
- Enter MLS number, buyer names, and plain-English offer terms.
- Extract common offer terms into a typed OfferData record.
- Validate required and conditional fields.
- Show what is complete and what still needs agent confirmation.

Material contract terms are never silently invented.

## Run locally
python -m venv .venv
Activate the environment, then:
pip install -r requirements.txt
uvicorn app.main:app --reload

Open http://127.0.0.1:8000

## V1 limitations
No MLS lookup, TransactionDesk connection, contract generation, LLM call, authentication, or draft persistence yet. Date parsing is deliberately conservative.

## Next milestone
Add an interactive clarification screen for missing conditional fields and revalidate until the offer reaches OFFER READY.
