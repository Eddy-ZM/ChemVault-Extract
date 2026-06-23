from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, require_document_permission
from app.extractors.pipeline import normalize_records_for_job
from app.models import ChemicalEntity, Document, ExtractionJob, MeasurementRecord, Project, ReactionRecord, User
from app.schemas import NormalizeResponse, NormalizationRequest
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/records", tags=["records"])


def _find_record_document_id(db: Session, record_type: str, record_id: str, user: User) -> tuple[str, str]:
    normalized = _normalize_record_type(record_type)
    if normalized is None:
        raise HTTPException(status_code=400, detail="Unsupported record type")

    if normalized == "chemical_entity":
        record = db.get(ChemicalEntity, record_id)
    elif normalized == "reaction":
        record = db.get(ReactionRecord, record_id)
    else:
        record = db.get(MeasurementRecord, record_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    require_document_permission(db, record.document_id, user, Permission.REVIEW)

    # Resolve the most recent AI job for this document to preserve status context.
    return (
        record.document_id,
        _find_latest_job_id(db, record.document_id),
    )


def _find_latest_job_id(db: Session, document_id: str) -> str | None:
    job = db.scalars(
        select(ExtractionJob)
        .where(ExtractionJob.document_id == document_id)
        .order_by(ExtractionJob.created_at.desc(), ExtractionJob.id.desc())
        .limit(1)
    ).first()
    return job.id if job is not None else None


def _normalize_record_type(value: str) -> str | None:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"chemical", "chemical_entity", "chemical-entity", "chemicalentity"}:
        return "chemical_entity"
    if normalized in {"reaction", "reaction_record", "reactionrecord"}:
        return "reaction"
    if normalized in {"measurement", "measurement_record", "measurementrecord"}:
        return "measurement"
    return None


@router.post("/{record_type}/{record_id}/renormalize", response_model=NormalizeResponse)
def renormalize_record(
    record_type: str,
    record_id: str,
    payload: NormalizationRequest | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NormalizeResponse:
    document_id, _ = _find_record_document_id(db, record_type, record_id, current_user)

    review_items = normalize_records_for_job(
        db,
        None,
        document_id=document_id,
        record_type=record_type,
        record_id=record_id,
        raw_data=payload.raw_data if payload else None,
    )
    db.commit()

    return NormalizeResponse.model_validate(
        {
            "status": "completed",
            "updated_records": len(review_items),
            "review_items": review_items,
        }
    )
