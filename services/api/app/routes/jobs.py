from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExtractionJob
from app.schemas import ExtractionJobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=ExtractionJobRead)
def get_job(job_id: str, db: Session = Depends(get_db)) -> ExtractionJobRead:
    job = db.get(ExtractionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return ExtractionJobRead.model_validate(job)
