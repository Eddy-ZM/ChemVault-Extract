from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, accessible_workspace_ids, require_project_permission
from app.billing.enforcement import assert_can_export
from app.database import get_db
from app.models import ExportJob, Project, User
from app.schemas import ExportJobCreateRequest, ExportJobRead
from app.security import get_current_user

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("", response_model=list[ExportJobRead])
def list_exports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ExportJobRead]:
    workspace_ids = accessible_workspace_ids(db, current_user)
    filters = [and_(Project.user_id == current_user.id, Project.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(Project.workspace_id.in_(workspace_ids))
    jobs = db.scalars(
        select(ExportJob)
        .join(Project, ExportJob.project_id == Project.id)
        .where(or_(*filters))
        .order_by(ExportJob.created_at.desc(), ExportJob.id.desc())
        .limit(50)
    ).all()
    return [ExportJobRead.model_validate(job) for job in jobs]


@router.post("", response_model=ExportJobRead, status_code=status.HTTP_201_CREATED)
def create_export(
    payload: ExportJobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportJobRead:
    access = require_project_permission(db, payload.project_id, current_user, Permission.EXPORT)
    assert_can_export(db, access.billing_user)
    project = access.project
    job = ExportJob(project_id=project.id, export_format=payload.export_format.strip() or "json")
    db.add(job)
    db.commit()
    db.refresh(job)
    return ExportJobRead.model_validate(job)
