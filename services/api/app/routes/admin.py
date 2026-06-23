from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.plans import PLAN_LIMITS, apply_plan_to_user
from app.database import get_db
from app.models import AiUsageRecord, AuditLog, User
from app.schemas import AdminPlanOverrideRequest, AiUsageRecordRead, UserRead
from app.security import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(_: User = Depends(get_current_admin_user), db: Session = Depends(get_db)) -> list[UserRead]:
    users = db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())).all()
    return [UserRead.model_validate(user) for user in users]


@router.get("/usage", response_model=list[AiUsageRecordRead])
def list_usage(_: User = Depends(get_current_admin_user), db: Session = Depends(get_db)) -> list[AiUsageRecordRead]:
    records = db.scalars(
        select(AiUsageRecord).order_by(AiUsageRecord.created_at.desc(), AiUsageRecord.id.desc()).limit(200)
    ).all()
    return [AiUsageRecordRead.model_validate(record) for record in records]


@router.post("/users/{user_id}/plan", response_model=UserRead)
def override_user_plan(
    user_id: str,
    payload: AdminPlanOverrideRequest,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> UserRead:
    plan = payload.plan.strip().lower()
    if plan not in PLAN_LIMITS:
        raise HTTPException(status_code=400, detail="Unsupported plan override.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user.plan_override = plan
    apply_plan_to_user(user, plan)
    db.add(
        AuditLog(
            actor_user_id=admin.id,
            target_user_id=user.id,
            action="admin.plan_override",
            reason=payload.reason,
            payload={"plan": plan},
        )
    )
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)
