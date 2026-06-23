from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.enforcement import first_day_of_current_month, get_current_usage
from app.constants import AiUsageStatus
from app.models import AiUsageRecord, Document, ExtractionJob, User


@dataclass(slots=True)
class CurrentMonthUsage:
    plan: str
    files_used: int
    files_limit: int
    estimated_cost_used_usd: float
    cost_limit_usd: float
    remaining_files: int
    remaining_cost_usd: float
    platform_estimated_cost_used_usd: float
    own_key_estimated_cost_used_usd: float
    projects_used: int
    projects_limit: int
    documents_used: int
    documents_limit: int
    storage_used_mb: float
    storage_limit_mb: int
    remaining_storage_mb: float
    can_export: bool
    can_batch_extract: bool


def current_month_usage(db: Session, user: User) -> CurrentMonthUsage:
    usage = get_current_usage(db, user)
    files_limit = usage.limits.monthly_ai_file_limit
    cost_limit = float(usage.limits.monthly_ai_cost_limit_usd)
    return CurrentMonthUsage(
        plan=usage.plan,
        files_used=usage.ai_files_used,
        files_limit=files_limit,
        estimated_cost_used_usd=usage.platform_ai_cost_used_usd,
        cost_limit_usd=round(cost_limit, 6),
        remaining_files=usage.remaining_files,
        remaining_cost_usd=usage.remaining_cost_usd,
        platform_estimated_cost_used_usd=usage.platform_ai_cost_used_usd,
        own_key_estimated_cost_used_usd=usage.own_key_ai_cost_used_usd,
        projects_used=usage.projects_used,
        projects_limit=usage.limits.max_projects,
        documents_used=usage.documents_used,
        documents_limit=usage.limits.max_documents,
        storage_used_mb=usage.storage_used_mb,
        storage_limit_mb=usage.limits.max_storage_mb,
        remaining_storage_mb=usage.remaining_storage_mb,
        can_export=usage.limits.can_export,
        can_batch_extract=usage.limits.can_batch_extract,
    )


def assert_monthly_ai_usage_allowed(db: Session, user: User, *, estimated_cost_usd: float) -> None:
    usage = current_month_usage(db, user)
    if usage.files_used >= usage.files_limit:
        raise HTTPException(status_code=400, detail="Monthly AI extraction file limit reached.")
    if usage.estimated_cost_used_usd + estimated_cost_usd > usage.cost_limit_usd:
        raise HTTPException(status_code=400, detail="Monthly AI cost limit reached.")


def create_ai_usage_record(
    db: Session,
    *,
    user: User,
    document: Document,
    job: ExtractionJob,
    provider: str,
    model: str,
    input_tokens_estimated: int,
    output_tokens_estimated: int,
    estimated_cost_usd: float,
    used_own_api_key: bool = False,
    usage_user: User | None = None,
    workspace_id: str | None = None,
    batch_job_id: str | None = None,
) -> AiUsageRecord:
    charged_user = usage_user or user
    record = AiUsageRecord(
        user_id=charged_user.id,
        project_id=document.project_id,
        workspace_id=workspace_id,
        batch_job_id=batch_job_id,
        document_id=document.id,
        extraction_job_id=job.id,
        provider=provider,
        model=model,
        input_tokens_estimated=input_tokens_estimated,
        output_tokens_estimated=output_tokens_estimated,
        estimated_cost_usd=estimated_cost_usd,
        platform_estimated_cost_usd=0.0 if used_own_api_key else estimated_cost_usd,
        user_paid_estimated_cost_usd=estimated_cost_usd if used_own_api_key else 0.0,
        used_own_api_key=used_own_api_key,
        is_user_provided_api_key=used_own_api_key,
        status=AiUsageStatus.ESTIMATED.value,
    )
    db.add(record)
    return record


def mark_ai_usage_completed(db: Session, extraction_job_id: str) -> None:
    for record in _usage_records_for_job(db, extraction_job_id):
        record.status = AiUsageStatus.COMPLETED.value
    db.commit()


def mark_ai_usage_failed(db: Session, extraction_job_id: str) -> None:
    for record in _usage_records_for_job(db, extraction_job_id):
        record.status = AiUsageStatus.FAILED.value
    db.commit()


def _usage_records_for_job(db: Session, extraction_job_id: str) -> list[AiUsageRecord]:
    return db.scalars(
        select(AiUsageRecord).where(AiUsageRecord.extraction_job_id == extraction_job_id)
    ).all()
