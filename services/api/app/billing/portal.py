from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.stripe_client import StripeClient
from app.config import Settings, get_settings
from app.models import Subscription, User


def create_customer_portal_session(db: Session, user: User, settings: Settings | None = None) -> str:
    resolved = settings or get_settings()
    subscription = db.scalars(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .limit(1)
    ).first()
    customer_id = subscription.stripe_customer_id if subscription else None
    if not customer_id and subscription:
        customer_id = subscription.external_customer_id
    if not customer_id:
        raise HTTPException(status_code=400, detail="Stripe customer does not exist yet.")
    session = StripeClient(resolved).create_customer_portal_session(
        customer_id=customer_id,
        return_url=resolved.stripe_customer_portal_return_url,
    )
    portal_url = session.get("url")
    if not portal_url:
        raise HTTPException(status_code=502, detail="Stripe did not return a portal URL.")
    return portal_url
