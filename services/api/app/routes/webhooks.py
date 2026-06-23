from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.billing.webhooks import handle_stripe_webhook
from app.database import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    raw_body = await request.body()
    signature = request.headers.get("stripe-signature")
    return handle_stripe_webhook(db, raw_body=raw_body, signature=signature)
