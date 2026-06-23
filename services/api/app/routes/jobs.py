from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, accessible_workspace_ids, require_document_permission
from app.database import get_db
from app.models import Document, ExtractionJob, Project, User
from app.schemas import ExtractionJobRead
from app.security import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=ExtractionJobRead)
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExtractionJobRead:
    workspace_ids = accessible_workspace_ids(db, current_user)
    filters = [and_(Project.user_id == current_user.id, Project.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(Project.workspace_id.in_(workspace_ids))
    job = db.scalars(
        select(ExtractionJob)
        .join(Document, ExtractionJob.document_id == Document.id)
        .join(Project, Document.project_id == Project.id)
        .where(ExtractionJob.id == job_id, or_(*filters))
    ).first()
    if job is not None:
        require_document_permission(db, job.document_id, current_user, Permission.VIEW)
        return ExtractionJobRead.model_validate(job)
    if db.get(ExtractionJob, job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    raise HTTPException(status_code=403, detail="You do not have access to this job.")
