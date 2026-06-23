from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.checkout import create_checkout_session
from app.billing.plans import get_effective_plan_limits
from app.billing.portal import create_customer_portal_session
from app.database import get_db
from app.models import Subscription, User
from app.schemas import (
    BillingOverviewRead,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CurrentMonthUsageRead,
    PlanLimitsRead,
    PortalSessionResponse,
    SubscriptionRead,
)
from app.security import get_current_user
from app.usage import current_month_usage

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/subscription", response_model=BillingOverviewRead)
def get_billing_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingOverviewRead:
    subscription = _latest_subscription(db, current_user)
    usage = current_month_usage(db, current_user)
    limits = get_effective_plan_limits(current_user)
    return BillingOverviewRead.model_validate(
        {
            "subscription": SubscriptionRead.model_validate(subscription) if subscription else None,
            "plan_limits": PlanLimitsRead.model_validate(limits.to_api()),
            "usage": CurrentMonthUsageRead.model_validate(asdict(usage)),
        }
    )


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session_endpoint(
    payload: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutSessionResponse:
    checkout_url = create_checkout_session(
        db,
        user=current_user,
        plan=payload.plan,
        billing_interval=payload.billing_interval,
    )
    db.commit()
    return CheckoutSessionResponse.model_validate({"checkout_url": checkout_url})


@router.post("/create-portal-session", response_model=PortalSessionResponse)
def create_portal_session_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortalSessionResponse:
    portal_url = create_customer_portal_session(db, current_user)
    return PortalSessionResponse.model_validate({"portal_url": portal_url})


def _latest_subscription(db: Session, user: User) -> Subscription | None:
    return db.scalars(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .limit(1)
    ).first()
