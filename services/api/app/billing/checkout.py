from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.plans import PlanName, get_price_id_for_plan
from app.billing.stripe_client import StripeClient
from app.config import Settings, get_settings
from app.constants import BillingInterval
from app.models import Subscription, User


def create_or_get_stripe_customer(db: Session, user: User, settings: Settings | None = None) -> str:
    resolved = settings or get_settings()
    subscription = _current_subscription(db, user)
    if subscription and subscription.stripe_customer_id:
        return subscription.stripe_customer_id
    if subscription and subscription.external_customer_id:
        subscription.stripe_customer_id = subscription.external_customer_id
        return subscription.stripe_customer_id

    customer = StripeClient(resolved).create_customer(email=user.email, name=user.name, user_id=user.id)
    customer_id = customer["id"]
    if subscription is None:
        subscription = Subscription(user_id=user.id, plan=user.plan)
        db.add(subscription)
    subscription.stripe_customer_id = customer_id
    subscription.external_customer_id = customer_id
    db.flush()
    return customer_id


def create_checkout_session(
    db: Session,
    *,
    user: User,
    plan: str,
    billing_interval: str,
    settings: Settings | None = None,
) -> str:
    resolved = settings or get_settings()
    plan = plan.lower()
    billing_interval = billing_interval.lower()
    if plan == PlanName.FREE.value:
        raise HTTPException(status_code=400, detail="Free plan does not require checkout.")
    if plan not in {PlanName.STUDENT.value, PlanName.RESEARCHER.value, PlanName.LAB.value}:
        raise HTTPException(status_code=400, detail="Unsupported billing plan.")
    if billing_interval not in {BillingInterval.MONTHLY.value, BillingInterval.YEARLY.value}:
        raise HTTPException(status_code=400, detail="Unsupported billing interval.")

    price_id = get_price_id_for_plan(plan, billing_interval, resolved)
    if not price_id:
        raise HTTPException(status_code=500, detail=f"Stripe price ID is missing for {plan} {billing_interval}.")

    customer_id = create_or_get_stripe_customer(db, user, resolved)
    session = StripeClient(resolved).create_checkout_session(
        customer_id=customer_id,
        price_id=price_id,
        user_id=user.id,
        plan=plan,
        success_url=resolved.stripe_checkout_success_url,
        cancel_url=resolved.stripe_checkout_cancel_url,
    )
    checkout_url = session.get("url")
    if not checkout_url:
        raise HTTPException(status_code=502, detail="Stripe did not return a checkout URL.")
    return checkout_url


def _current_subscription(db: Session, user: User) -> Subscription | None:
    return db.scalars(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .limit(1)
    ).first()
