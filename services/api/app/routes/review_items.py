from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.constants import ReviewStatus
from app.database import get_db
from app.models import ReviewItem
from app.schemas import ReviewItemRead, ReviewItemUpdate

router = APIRouter(prefix="/review-items", tags=["review-items"])


@router.patch("/{review_item_id}", response_model=ReviewItemRead)
def update_review_item(
    review_item_id: str,
    payload: ReviewItemUpdate,
    db: Session = Depends(get_db),
) -> ReviewItemRead:
    item = db.get(ReviewItem, review_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Review item not found")

    if payload.status is not None:
        if payload.status not in {status.value for status in ReviewStatus}:
            raise HTTPException(status_code=400, detail="Unsupported review status")
        item.status = payload.status
    if payload.extractedData is not None:
        item.extracted_data = payload.extractedData

    db.commit()
    db.refresh(item)
    return ReviewItemRead.model_validate(item)
