from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.billing.plans import PlanLimits, get_effective_plan, get_effective_plan_limits
from app.constants import AiUsageStatus
from app.models import AiUsageRecord, Document, Project, User, Workspace, WorkspaceMember


@dataclass(slots=True)
class BillingUsage:
    plan: str
    limits: PlanLimits
    projects_used: int
    documents_used: int
    storage_used_mb: float
    ai_files_used: int
    platform_ai_cost_used_usd: float
    own_key_ai_cost_used_usd: float

    @property
    def ai_cost_used_usd(self) -> float:
        return self.platform_ai_cost_used_usd

    @property
    def remaining_files(self) -> int:
        return max(self.limits.monthly_ai_file_limit - self.ai_files_used, 0)

    @property
    def remaining_cost_usd(self) -> float:
        return round(max(self.limits.monthly_ai_cost_limit_usd - self.platform_ai_cost_used_usd, 0.0), 6)

    @property
    def remaining_storage_mb(self) -> float:
        return round(max(self.limits.max_storage_mb - self.storage_used_mb, 0.0), 6)


def first_day_of_current_month() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc)


def get_current_usage(db: Session, user: User, workspace: Workspace | None = None) -> BillingUsage:
    month_start = first_day_of_current_month()
    limits = _limits_for_user(user)
    project_filter = _project_scope_filter(db, user, workspace)
    usage_user_id = workspace.owner_user_id if workspace is not None else user.id
    workspace_filter = [AiUsageRecord.workspace_id == workspace.id] if workspace is not None else []

    projects_used = db.scalar(select(func.count(Project.id)).where(project_filter)) or 0
    documents_used = (
        db.scalar(
            select(func.count(Document.id))
            .join(Project, Document.project_id == Project.id)
            .where(project_filter)
        )
        or 0
    )
    storage_bytes = (
        db.scalar(
            select(func.coalesce(func.sum(Document.file_size_bytes), 0))
            .join(Project, Document.project_id == Project.id)
            .where(project_filter)
        )
        or 0
    )
    ai_files_used = (
        db.scalar(
            select(func.count(AiUsageRecord.id)).where(
                AiUsageRecord.user_id == usage_user_id,
                AiUsageRecord.status == AiUsageStatus.COMPLETED.value,
                AiUsageRecord.created_at >= month_start,
                *workspace_filter,
            )
        )
        or 0
    )
    platform_cost = (
        db.scalar(
            select(func.coalesce(func.sum(AiUsageRecord.platform_estimated_cost_usd), 0.0)).where(
                AiUsageRecord.user_id == usage_user_id,
                AiUsageRecord.status == AiUsageStatus.COMPLETED.value,
                AiUsageRecord.created_at >= month_start,
                *workspace_filter,
            )
        )
        or 0.0
    )
    own_key_cost = (
        db.scalar(
            select(func.coalesce(func.sum(AiUsageRecord.user_paid_estimated_cost_usd), 0.0)).where(
                AiUsageRecord.user_id == usage_user_id,
                AiUsageRecord.status == AiUsageStatus.COMPLETED.value,
                AiUsageRecord.created_at >= month_start,
                *workspace_filter,
            )
        )
        or 0.0
    )
    return BillingUsage(
        plan=get_effective_plan(user),
        limits=limits,
        projects_used=int(projects_used),
        documents_used=int(documents_used),
        storage_used_mb=round(float(storage_bytes) / (1024 * 1024), 6),
        ai_files_used=int(ai_files_used),
        platform_ai_cost_used_usd=round(float(platform_cost), 6),
        own_key_ai_cost_used_usd=round(float(own_key_cost), 6),
    )


def _project_scope_filter(db: Session, user: User, workspace: Workspace | None = None):
    if workspace is not None:
        return Project.workspace_id == workspace.id
    owned_workspace_ids = db.scalars(select(Workspace.id).where(Workspace.owner_user_id == user.id)).all()
    if owned_workspace_ids:
        return or_(
            and_(Project.user_id == user.id, Project.workspace_id.is_(None)),
            Project.workspace_id.in_(owned_workspace_ids),
        )
    return and_(Project.user_id == user.id, Project.workspace_id.is_(None))


def _limits_for_user(user: User) -> PlanLimits:
    limits = get_effective_plan_limits(user)
    return replace(
        limits,
        monthly_ai_file_limit=user.monthly_ai_file_limit or limits.monthly_ai_file_limit,
        monthly_ai_cost_limit_usd=user.monthly_ai_cost_limit_usd or limits.monthly_ai_cost_limit_usd,
    )


def assert_can_create_workspace(user: User) -> None:
    usage = get_effective_plan(user)
    if usage not in {"lab", "admin"}:
        raise HTTPException(status_code=403, detail="Your current plan does not support team workspaces.")


def assert_can_create_project(db: Session, user: User, workspace: Workspace | None = None) -> None:
    usage = get_current_usage(db, user, workspace)
    if usage.projects_used >= usage.limits.max_projects:
        raise HTTPException(status_code=400, detail="Project limit reached for current plan.")


def assert_can_upload_document(
    db: Session,
    user: User,
    *,
    file_size_bytes: int,
    workspace: Workspace | None = None,
) -> None:
    usage = get_current_usage(db, user, workspace)
    if usage.documents_used >= usage.limits.max_documents:
        raise HTTPException(status_code=400, detail="Document limit reached for current plan.")
    upload_mb = file_size_bytes / (1024 * 1024)
    if usage.storage_used_mb + upload_mb > usage.limits.max_storage_mb:
        raise HTTPException(status_code=400, detail="Storage limit reached for current plan.")


def assert_can_batch_upload(
    db: Session,
    user: User,
    *,
    total_file_size_bytes: int,
    file_count: int,
    workspace: Workspace | None = None,
) -> None:
    usage = get_current_usage(db, user, workspace)
    if usage.documents_used + file_count > usage.limits.max_documents:
        raise HTTPException(status_code=400, detail="Document limit reached for current plan.")
    upload_mb = total_file_size_bytes / (1024 * 1024)
    if usage.storage_used_mb + upload_mb > usage.limits.max_storage_mb:
        raise HTTPException(status_code=400, detail="Storage limit reached for current plan.")


def assert_can_run_ai_extraction(
    db: Session,
    user: User,
    *,
    estimated_cost_usd: float,
    counts_platform_cost: bool,
    file_count: int = 1,
    workspace: Workspace | None = None,
) -> None:
    usage = get_current_usage(db, user, workspace)
    if usage.ai_files_used + file_count > usage.limits.monthly_ai_file_limit:
        raise HTTPException(status_code=400, detail="Monthly AI extraction file limit reached.")
    if counts_platform_cost and usage.platform_ai_cost_used_usd + estimated_cost_usd > usage.limits.monthly_ai_cost_limit_usd:
        raise HTTPException(status_code=400, detail="Monthly AI cost limit reached.")


def assert_can_export(db: Session, user: User) -> None:
    if not get_current_usage(db, user).limits.can_export:
        raise HTTPException(status_code=403, detail="Export is not available on current plan.")


def assert_can_batch_extract(db: Session, user: User, workspace: Workspace | None = None) -> None:
    if not get_current_usage(db, user, workspace).limits.can_batch_extract:
        raise HTTPException(status_code=403, detail="Batch extraction is not available on current plan.")


def assert_can_invite_member(db: Session, user: User, workspace: Workspace) -> None:
    limits = get_current_usage(db, workspace.owner).limits
    member_count = db.scalar(
        select(func.count(WorkspaceMember.id)).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.status.in_(["invited", "active"]),
        )
    ) or 0
    if int(member_count) >= limits.team_members:
        raise HTTPException(status_code=400, detail="Team member limit reached for current plan.")


def assert_workspace_storage_limit(db: Session, workspace: Workspace) -> None:
    usage = get_current_usage(db, workspace.owner, workspace)
    if usage.storage_used_mb > usage.limits.max_storage_mb:
        raise HTTPException(status_code=400, detail="Storage limit reached for current plan.")


def assert_workspace_document_limit(db: Session, workspace: Workspace) -> None:
    usage = get_current_usage(db, workspace.owner, workspace)
    if usage.documents_used > usage.limits.max_documents:
        raise HTTPException(status_code=400, detail="Document limit reached for current plan.")
