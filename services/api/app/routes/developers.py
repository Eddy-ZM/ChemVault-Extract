from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.billing.plans import get_effective_plan
from app.database import get_db
from app.models import AiUsageRecord, ApiKey, ApiRequestLog, User
from app.rate_limit import RATE_LIMITS
from app.schemas import ApiRequestLogRead, DeveloperUsageRead
from app.security import get_current_user
from app.usage import first_day_of_current_month

router = APIRouter(prefix="/developers", tags=["developers"])


@router.get("/logs", response_model=list[ApiRequestLogRead])
def list_developer_api_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ApiRequestLogRead]:
    logs = db.scalars(
        select(ApiRequestLog)
        .where(ApiRequestLog.user_id == current_user.id)
        .order_by(ApiRequestLog.created_at.desc(), ApiRequestLog.id.desc())
        .limit(100)
    ).all()
    return [ApiRequestLogRead.model_validate(log) for log in logs]


@router.get("/usage", response_model=DeveloperUsageRead)
def get_developer_api_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeveloperUsageRead:
    month_start = first_day_of_current_month()
    requests_this_month = db.scalar(
        select(func.count(ApiRequestLog.id)).where(
            ApiRequestLog.user_id == current_user.id,
            ApiRequestLog.created_at >= month_start,
        )
    ) or 0
    active_keys = db.scalar(
        select(func.count(ApiKey.id)).where(
            ApiKey.user_id == current_user.id,
            ApiKey.revoked_at.is_(None),
        )
    ) or 0
    extraction_jobs = db.scalar(
        select(func.count(ApiRequestLog.id)).where(
            ApiRequestLog.user_id == current_user.id,
            ApiRequestLog.method == "POST",
            ApiRequestLog.path.like("/v1/documents/%/extract"),
            ApiRequestLog.status_code < 400,
            ApiRequestLog.created_at >= month_start,
        )
    ) or 0
    estimated_ai_cost = db.scalar(
        select(func.coalesce(func.sum(AiUsageRecord.estimated_cost_usd), 0.0)).where(
            and_(AiUsageRecord.user_id == current_user.id, AiUsageRecord.created_at >= month_start)
        )
    ) or 0.0
    plan = get_effective_plan(current_user)
    return DeveloperUsageRead.model_validate(
        {
            "requests_this_month": requests_this_month,
            "api_keys_active": active_keys,
            "extraction_jobs_created_by_api": extraction_jobs,
            "estimated_ai_cost_usd": round(float(estimated_ai_cost), 6),
            "rate_limit": RATE_LIMITS.get(plan, RATE_LIMITS["free"]),
        }
    )
