from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, accessible_workspace_ids, require_project_permission, workspace_access
from app.database import get_db
from app.models import ChemicalEntity, Document, MeasurementRecord, Project, ReactionRecord, User
from app.security import get_current_user

router = APIRouter(prefix="/database", tags=["database"])


@router.get("")
def scientific_database(
    workspace_id: str | None = None,
    project_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project_ids = _accessible_project_ids(db, current_user, workspace_id=workspace_id, project_id=project_id)
    if not project_ids:
        return {"chemicalEntities": [], "reactions": [], "measurements": []}
    document_ids = db.scalars(select(Document.id).where(Document.project_id.in_(project_ids))).all()
    if not document_ids:
        return {"chemicalEntities": [], "reactions": [], "measurements": []}
    chemicals = db.scalars(select(ChemicalEntity).where(ChemicalEntity.document_id.in_(document_ids))).all()
    reactions = db.scalars(select(ReactionRecord).where(ReactionRecord.document_id.in_(document_ids))).all()
    measurements = db.scalars(select(MeasurementRecord).where(MeasurementRecord.document_id.in_(document_ids))).all()
    return {
        "chemicalEntities": [_record_payload(item) for item in chemicals],
        "reactions": [_record_payload(item) for item in reactions],
        "measurements": [_record_payload(item) for item in measurements],
    }


def _accessible_project_ids(
    db: Session,
    user: User,
    *,
    workspace_id: str | None,
    project_id: str | None,
) -> list[str]:
    if project_id:
        access = require_project_permission(db, project_id, user, Permission.VIEW)
        if workspace_id and access.workspace_id != workspace_id:
            return []
        return [access.project.id]
    if workspace_id:
        workspace_access(db, workspace_id, user)
        return db.scalars(select(Project.id).where(Project.workspace_id == workspace_id)).all()
    workspace_ids = accessible_workspace_ids(db, user)
    filters = [and_(Project.user_id == user.id, Project.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(Project.workspace_id.in_(workspace_ids))
    return db.scalars(select(Project.id).where(or_(*filters))).all()


def _record_payload(record) -> dict:
    return {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
        if column.name not in {"storage_key"}
    }
