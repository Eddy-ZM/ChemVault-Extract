from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, accessible_workspace_ids, require_project_permission, workspace_access
from app.database import get_db
from app.models import ChemicalEntity, Document, DocumentChunk, MeasurementRecord, Project, ReactionRecord, ReviewItem, User
from app.security import get_current_user

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = "",
    workspace_id: str | None = None,
    project_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = q.strip()
    project_ids = _accessible_project_ids(db, current_user, workspace_id=workspace_id, project_id=project_id)
    if not project_ids or not query:
        return {"documents": [], "chunks": [], "records": []}

    like = f"%{query}%"
    documents = db.scalars(
        select(Document)
        .where(
            Document.project_id.in_(project_ids),
            or_(Document.filename.ilike(like), Document.original_filename.ilike(like), Document.file_type.ilike(like)),
        )
        .order_by(Document.created_at.desc())
        .limit(50)
    ).all()
    chunks = db.scalars(
        select(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.project_id.in_(project_ids), DocumentChunk.text.ilike(like))
        .order_by(DocumentChunk.created_at.desc())
        .limit(50)
    ).all()
    records = _search_records(db, project_ids, like)
    return {
        "documents": [
            {
                "id": item.id,
                "projectId": item.project_id,
                "filename": item.filename,
                "fileType": item.file_type,
                "status": item.status,
            }
            for item in documents
        ],
        "chunks": [
            {
                "id": item.id,
                "documentId": item.document_id,
                "section": item.section,
                "pageStart": item.page_start,
                "pageEnd": item.page_end,
                "text": item.text[:600],
            }
            for item in chunks
        ],
        "records": records,
    }


def _search_records(db: Session, project_ids: list[str], like: str) -> list[dict]:
    document_ids = db.scalars(select(Document.id).where(Document.project_id.in_(project_ids))).all()
    if not document_ids:
        return []

    records: list[dict] = []
    for model, record_type, fields, label_builder in (
        (
            ChemicalEntity,
            "chemical_entity",
            [ChemicalEntity.name, ChemicalEntity.raw_name, ChemicalEntity.normalized_name, ChemicalEntity.role, ChemicalEntity.formula],
            lambda row: row.normalized_name or row.raw_name or row.name,
        ),
        (
            ReactionRecord,
            "reaction",
            [ReactionRecord.reaction_name, ReactionRecord.raw_yield_value, ReactionRecord.normalized_yield_value],
            lambda row: row.reaction_name or "Reaction record",
        ),
        (
            MeasurementRecord,
            "measurement",
            [MeasurementRecord.measurement_type, MeasurementRecord.normalized_measurement_type, MeasurementRecord.subject, MeasurementRecord.raw_value],
            lambda row: row.normalized_measurement_type or row.measurement_type,
        ),
    ):
        matches = (
            db.scalars(
                select(model)
                .join(ReviewItem, ReviewItem.record_id == model.id)
                .where(
                    model.document_id.in_(document_ids),
                    ReviewItem.record_type == record_type,
                    ReviewItem.status != "rejected",
                    or_(*[field.ilike(like) for field in fields]),
                )
                .order_by(model.created_at.desc(), model.id.desc())
                .limit(50)
            )
            .unique()
            .all()
        )
        for row in matches:
            evidence = row.evidence if isinstance(row.evidence, dict) else {}
            records.append(
                {
                    "id": row.id,
                    "documentId": row.document_id,
                    "recordType": record_type,
                    "label": label_builder(row),
                    "reviewStatus": _review_status(db, row.document_id, record_type, row.id),
                    "validationStatus": getattr(row, "validation_status", None),
                    "confidence": getattr(row, "confidence", None),
                    "evidence": evidence,
                    "preview": evidence.get("quote") or _record_preview(row),
                }
            )
    return records[:100]


def _review_status(db: Session, document_id: str, record_type: str, record_id: str) -> str | None:
    item = db.scalars(
        select(ReviewItem)
        .where(ReviewItem.document_id == document_id, ReviewItem.record_type == record_type, ReviewItem.record_id == record_id)
        .order_by(ReviewItem.created_at.desc(), ReviewItem.id.desc())
        .limit(1)
    ).first()
    return item.status if item else None


def _record_preview(row) -> str:
    if isinstance(row, ChemicalEntity):
        return " ".join(value for value in [row.raw_name, row.normalized_name, row.formula, row.role] if value)
    if isinstance(row, ReactionRecord):
        return " ".join(value for value in [row.reaction_name, row.raw_yield_value, row.raw_yield_unit] if value)
    if isinstance(row, MeasurementRecord):
        return " ".join(value for value in [row.measurement_type, row.subject, row.raw_value, row.raw_unit] if value)
    return ""


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
