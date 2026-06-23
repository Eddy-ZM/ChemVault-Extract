from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.orm import Session

from app.billing.plans import apply_plan_to_user, get_plan_from_stripe_price_id
from app.billing.stripe_client import StripeClient
from app.config import Settings, get_settings
from app.constants import BillingInterval, SubscriptionStatus, UserPlan
from app.models import BillingEvent, Subscription, User


ACTIVE_STRIPE_STATUSES = {SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value}
RESTRICTED_STRIPE_STATUSES = {
    SubscriptionStatus.PAST_DUE.value,
    SubscriptionStatus.UNPAID.value,
    SubscriptionStatus.CANCELLED.value,
    SubscriptionStatus.INCOMPLETE_EXPIRED.value,
}


def handle_stripe_webhook(
    db: Session,
    *,
    raw_body: bytes,
    signature: str | None,
    settings: Settings | None = None,
) -> dict[str, str]:
    resolved = settings or get_settings()
    event = verify_stripe_signature(raw_body, signature, resolved)
    event_id = event.get("id")
    event_type = event.get("type")
    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="Invalid Stripe event.")

    if db.scalars(select(BillingEvent).where(BillingEvent.stripe_event_id == event_id)).first() is not None:
        return {"status": "duplicate"}

    user_id = _process_event(db, event, resolved)
    db.add(
        BillingEvent(
            user_id=user_id,
            stripe_event_id=event_id,
            event_type=event_type,
            payload=event,
        )
    )
    db.commit()
    return {"status": "processed"}


def verify_stripe_signature(raw_body: bytes, signature: str | None, settings: Settings | None = None) -> dict[str, Any]:
    resolved = settings or get_settings()
    if not resolved.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET is missing.")
    if not signature:
        raise HTTPException(status_code=400, detail="Stripe signature is missing.")

    timestamp: str | None = None
    signatures: list[str] = []
    for part in signature.split(","):
        key, _, value = part.partition("=")
        if key == "t":
            timestamp = value
        elif key == "v1":
            signatures.append(value)
    if not timestamp or not signatures:
        raise HTTPException(status_code=400, detail="Stripe signature is invalid.")

    try:
        timestamp_int = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Stripe signature timestamp is invalid.") from exc
    if abs(time.time() - timestamp_int) > 300:
        raise HTTPException(status_code=400, detail="Stripe signature timestamp is outside tolerance.")

    payload = raw_body.decode("utf-8")
    signed_payload = f"{timestamp}.{payload}".encode("utf-8")
    expected = hmac.new(resolved.stripe_webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, value) for value in signatures):
        raise HTTPException(status_code=400, detail="Stripe signature verification failed.")
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Stripe event body is invalid JSON.") from exc


def sync_subscription_from_stripe(
    db: Session,
    subscription_payload: dict[str, Any],
    settings: Settings | None = None,
) -> str | None:
    resolved = settings or get_settings()
    user = _user_for_subscription_payload(db, subscription_payload)
    if user is None:
        raise HTTPException(status_code=400, detail="Could not map Stripe subscription to a user.")

    price_id = _price_id_from_subscription(subscription_payload)
    plan = get_plan_from_stripe_price_id(price_id, resolved) or UserPlan.FREE.value
    status = subscription_payload.get("status") or SubscriptionStatus.INCOMPLETE.value
    subscription = _get_or_create_subscription(db, user, subscription_payload)
    subscription.plan = plan
    subscription.status = status
    subscription.billing_interval = _billing_interval_from_subscription(subscription_payload)
    subscription.stripe_customer_id = _id_or_value(subscription_payload.get("customer"))
    subscription.external_customer_id = subscription.stripe_customer_id
    subscription.stripe_subscription_id = subscription_payload.get("id")
    subscription.external_subscription_id = subscription.stripe_subscription_id
    subscription.stripe_price_id = price_id
    subscription.current_period_start = _dt(subscription_payload.get("current_period_start"))
    subscription.current_period_end = _dt(subscription_payload.get("current_period_end"))
    subscription.cancel_at_period_end = bool(subscription_payload.get("cancel_at_period_end"))
    subscription.trial_end = _dt(subscription_payload.get("trial_end"))
    subscription.latest_invoice_id = _id_or_value(subscription_payload.get("latest_invoice"))

    if status in ACTIVE_STRIPE_STATUSES:
        apply_plan_to_user(user, plan)
    elif status in RESTRICTED_STRIPE_STATUSES or subscription_payload.get("object") == "subscription":
        apply_plan_to_user(user, UserPlan.FREE.value)
    db.flush()
    return user.id


def _process_event(db: Session, event: dict[str, Any], settings: Settings) -> str | None:
    event_type = event["type"]
    data_object = event.get("data", {}).get("object", {})
    if event_type == "checkout.session.completed":
        return _handle_checkout_completed(db, data_object, settings)
    if event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        if event_type == "customer.subscription.deleted":
            data_object["status"] = SubscriptionStatus.CANCELLED.value
        return sync_subscription_from_stripe(db, data_object, settings)
    if event_type == "invoice.payment_succeeded":
        return _handle_invoice_status(db, data_object, payment_status="paid")
    if event_type == "invoice.payment_failed":
        return _handle_invoice_status(db, data_object, payment_status="failed", force_status=SubscriptionStatus.PAST_DUE.value)
    return None


def _handle_checkout_completed(db: Session, session: dict[str, Any], settings: Settings) -> str | None:
    subscription_id = _id_or_value(session.get("subscription"))
    user_id = (session.get("metadata") or {}).get("userId")
    user = db.get(User, user_id) if user_id else None
    if user:
        subscription = _latest_subscription_for_user(db, user)
        if subscription is None:
            subscription = Subscription(user_id=user.id, plan=UserPlan.FREE.value)
            db.add(subscription)
        subscription.stripe_customer_id = _id_or_value(session.get("customer"))
        subscription.external_customer_id = subscription.stripe_customer_id
        subscription.stripe_subscription_id = subscription_id
        subscription.external_subscription_id = subscription_id
        db.flush()
    if subscription_id:
        subscription_payload = StripeClient(settings).retrieve_subscription(subscription_id)
        return sync_subscription_from_stripe(db, subscription_payload, settings)
    return user.id if user else None


def _handle_invoice_status(
    db: Session,
    invoice: dict[str, Any],
    *,
    payment_status: str,
    force_status: str | None = None,
) -> str | None:
    subscription_id = _id_or_value(invoice.get("subscription"))
    customer_id = _id_or_value(invoice.get("customer"))
    conditions: list[ColumnElement[bool]] = []
    if subscription_id:
        conditions.extend(
            [
                Subscription.stripe_subscription_id == subscription_id,
                Subscription.external_subscription_id == subscription_id,
            ]
        )
    if customer_id:
        conditions.append(Subscription.stripe_customer_id == customer_id)
    if not conditions:
        return None
    condition = conditions[0]
    for item in conditions[1:]:
        condition = condition | item
    subscription = db.scalars(select(Subscription).where(condition)).first()
    if subscription is None:
        return None
    subscription.latest_invoice_id = invoice.get("id")
    subscription.last_payment_status = payment_status
    if force_status:
        subscription.status = force_status
        user = db.get(User, subscription.user_id)
        if user:
            apply_plan_to_user(user, UserPlan.FREE.value)
    db.flush()
    return subscription.user_id


def _user_for_subscription_payload(db: Session, payload: dict[str, Any]) -> User | None:
    metadata = payload.get("metadata") or {}
    user_id = metadata.get("userId")
    if user_id:
        user = db.get(User, user_id)
        if user:
            return user
    subscription_id = payload.get("id")
    customer_id = _id_or_value(payload.get("customer"))
    conditions: list[ColumnElement[bool]] = []
    if subscription_id:
        conditions.extend(
            [
                Subscription.stripe_subscription_id == subscription_id,
                Subscription.external_subscription_id == subscription_id,
            ]
        )
    if customer_id:
        conditions.extend(
            [
                Subscription.stripe_customer_id == customer_id,
                Subscription.external_customer_id == customer_id,
            ]
        )
    if not conditions:
        return None
    condition = conditions[0]
    for item in conditions[1:]:
        condition = condition | item
    subscription = db.scalars(select(Subscription).where(condition)).first()
    return db.get(User, subscription.user_id) if subscription else None


def _get_or_create_subscription(db: Session, user: User, payload: dict[str, Any]) -> Subscription:
    subscription_id = payload.get("id")
    if subscription_id:
        subscription = db.scalars(
            select(Subscription).where(
                (Subscription.stripe_subscription_id == subscription_id)
                | (Subscription.external_subscription_id == subscription_id)
            )
        ).first()
        if subscription:
            return subscription
    subscription = _latest_subscription_for_user(db, user)
    if subscription is None:
        subscription = Subscription(user_id=user.id, plan=UserPlan.FREE.value)
        db.add(subscription)
    return subscription


def _latest_subscription_for_user(db: Session, user: User) -> Subscription | None:
    return db.scalars(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .limit(1)
    ).first()


def _price_id_from_subscription(payload: dict[str, Any]) -> str | None:
    items = payload.get("items", {}).get("data") or []
    if not items:
        return None
    price = items[0].get("price") or {}
    return price.get("id")


def _billing_interval_from_subscription(payload: dict[str, Any]) -> str | None:
    items = payload.get("items", {}).get("data") or []
    if not items:
        return None
    recurring = (items[0].get("price") or {}).get("recurring") or {}
    interval = recurring.get("interval")
    if interval == "year":
        return BillingInterval.YEARLY.value
    if interval == "month":
        return BillingInterval.MONTHLY.value
    return None


def _dt(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def _id_or_value(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("id")
    return value
