from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, accessible_workspace_ids, require_project_permission, workspace_access
from app.database import get_db
from app.models import Document, DocumentChunk, Project, User
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
        return {"documents": [], "chunks": []}

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
