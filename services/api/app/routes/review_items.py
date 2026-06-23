from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, accessible_workspace_ids, require_document_permission
from app.constants import ReviewStatus
from app.database import get_db
from app.models import Document, Project, ReviewItem, User
from app.schemas import ReviewItemRead, ReviewItemUpdate
from app.security import get_current_user
from app.webhook_delivery import enqueue_webhook_event_for_document

router = APIRouter(prefix="/review-items", tags=["review-items"])


@router.get("", response_model=list[ReviewItemRead])
def list_review_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReviewItemRead]:
    workspace_ids = accessible_workspace_ids(db, current_user)
    filters = [and_(Project.user_id == current_user.id, Project.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(Project.workspace_id.in_(workspace_ids))
    items = db.scalars(
        select(ReviewItem)
        .join(Document, ReviewItem.document_id == Document.id)
        .join(Project, Document.project_id == Project.id)
        .where(or_(*filters))
        .order_by(ReviewItem.created_at.desc(), ReviewItem.id.desc())
        .limit(50)
    ).all()
    return [ReviewItemRead.model_validate(item) for item in items]


@router.patch("/{review_item_id}", response_model=ReviewItemRead)
def update_review_item(
    review_item_id: str,
    payload: ReviewItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewItemRead:
    item = db.scalars(
        select(ReviewItem)
        .join(Document, ReviewItem.document_id == Document.id)
        .join(Project, Document.project_id == Project.id)
        .where(ReviewItem.id == review_item_id)
    ).first()
    if item is None and db.get(ReviewItem, review_item_id) is None:
        raise HTTPException(status_code=404, detail="Review item not found")
    if item is None:
        raise HTTPException(status_code=403, detail="You do not have access to this review item.")
    require_document_permission(db, item.document_id, current_user, Permission.REVIEW)

    previous_status = item.status
    if payload.status is not None:
        if payload.status not in {status.value for status in ReviewStatus}:
            raise HTTPException(status_code=400, detail="Unsupported review status")
        item.status = payload.status
    if payload.extractedData is not None:
        item.extracted_data = payload.extractedData

    if item.status != previous_status and item.status in {ReviewStatus.APPROVED.value, ReviewStatus.REJECTED.value}:
        event_type = "review.item_approved" if item.status == ReviewStatus.APPROVED.value else "review.item_rejected"
        enqueue_webhook_event_for_document(
            db,
            None,
            document=item.document,
            event_type=event_type,
            data={
                "review_item_id": item.id,
                "record_type": item.record_type,
                "record_id": item.record_id,
                "status": item.status,
            },
        )

    db.commit()
    db.refresh(item)
    return ReviewItemRead.model_validate(item)
