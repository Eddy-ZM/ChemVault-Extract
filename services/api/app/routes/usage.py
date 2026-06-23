from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AiUsageRecord, User
from app.schemas import AiUsageRecordRead, CurrentMonthUsageRead
from app.security import get_current_user
from app.usage import current_month_usage, first_day_of_current_month

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/current-month", response_model=CurrentMonthUsageRead)
def get_current_month_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentMonthUsageRead:
    usage = current_month_usage(db, current_user)
    recent = db.scalars(
        select(AiUsageRecord)
        .where(AiUsageRecord.user_id == current_user.id, AiUsageRecord.created_at >= first_day_of_current_month())
        .order_by(AiUsageRecord.created_at.desc(), AiUsageRecord.id.desc())
        .limit(20)
    ).all()
    return CurrentMonthUsageRead.model_validate(
        {
            **asdict(usage),
            "recent_records": [AiUsageRecordRead.model_validate(record) for record in recent],
        }
    )
