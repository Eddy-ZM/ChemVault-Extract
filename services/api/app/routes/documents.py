import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.config.ai import estimate_ai_cost_for_chunks, get_ai_settings
from app.constants import DocumentStatus, JobStatus, JobType
from app.database import get_db
from app.dependencies import get_queue, get_storage
from app.models import (
    ChemicalEntity,
    Document,
    DocumentBlock,
    DocumentChunk,
    DocumentPage,
    ExtractionJob,
    MeasurementRecord,
    Project,
    ReactionRecord,
    ReviewItem,
    User,
)
from app.queue import JobQueue
from app.schemas import (
    AICostEstimateRead,
    AIExtractionJobResponse,
    DocumentBlockRead,
    DocumentChunkRead,
    DocumentExtractionsRead,
    DocumentPageRead,
    DocumentWithLatestJob,
    ExtractionJobRead,
    ReviewItemRead,
    UploadDocumentResponse,
)
from app.storage import S3Storage, sanitize_filename, validate_upload_file

router = APIRouter(prefix="/documents", tags=["documents"])


def _latest_job(db: Session, document_id: str) -> ExtractionJob | None:
    return db.scalars(
        select(ExtractionJob)
        .where(ExtractionJob.document_id == document_id)
        .order_by(ExtractionJob.created_at.desc(), ExtractionJob.id.desc())
        .limit(1)
    ).first()


def _document_response(db: Session, document: Document) -> DocumentWithLatestJob:
    latest = _latest_job(db, document.id)
    return DocumentWithLatestJob.model_validate(document).model_copy(
        update={"latest_job": ExtractionJobRead.model_validate(latest) if latest else None}
    )


def _get_or_create_default_project(db: Session) -> Project:
    settings = get_settings()
    user = db.scalars(select(User).where(User.email == settings.default_user_email)).first()
    if user is None:
        user = User(email=settings.default_user_email, name="Local User")
        db.add(user)
        db.flush()

    project = db.scalars(
        select(Project).where(
            Project.user_id == user.id,
            Project.name == settings.default_project_name,
        )
    ).first()
    if project is None:
        project = Project(user_id=user.id, name=settings.default_project_name)
        db.add(project)
        db.flush()
    return project


def _first_day_of_current_month() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc)


def _count_successful_ai_jobs_this_month(db: Session) -> int:
    return len(
        db.scalars(
            select(ExtractionJob).where(
                ExtractionJob.job_type == JobType.AI_EXTRACTION.value,
                ExtractionJob.status == JobStatus.REVIEW_READY.value,
                ExtractionJob.created_at >= _first_day_of_current_month(),
            )
        ).all()
    )


def _assert_ai_extraction_allowed(db: Session) -> None:
    settings = get_settings()
    ai_settings = get_ai_settings(settings)
    if ai_settings.provider == "openai" and not ai_settings.openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY is missing. Please configure it before running AI extraction.",
        )
    if _count_successful_ai_jobs_this_month(db) >= ai_settings.monthly_free_file_limit:
        raise HTTPException(status_code=400, detail="Monthly AI extraction limit reached.")


def _document_chunks_for_ai(db: Session, document_id: str) -> list[DocumentChunk]:
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Document has no parsed chunks. Parse the document before running AI extraction.",
        )
    return chunks


def _ai_cost_estimate_response(document_id: str, chunks: list[DocumentChunk]) -> AICostEstimateRead:
    settings = get_settings()
    ai_settings = get_ai_settings(settings)
    estimate = estimate_ai_cost_for_chunks(document_id=document_id, chunks=chunks, ai_settings=ai_settings)
    return AICostEstimateRead.model_validate(
        {
            "document_id": estimate.document_id,
            "selected_chunks": estimate.selected_chunks,
            "estimated_input_tokens": estimate.estimated_input_tokens,
            "estimated_output_tokens": estimate.estimated_output_tokens,
            "model": estimate.model,
            "estimated_cost_usd": estimate.estimated_cost_usd,
            "warning": estimate.warning,
        }
    )


@router.get("", response_model=list[DocumentWithLatestJob])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentWithLatestJob]:
    documents = db.scalars(select(Document).order_by(Document.created_at.desc(), Document.id.desc())).all()
    return [_document_response(db, document) for document in documents]


@router.get("/{document_id}", response_model=DocumentWithLatestJob)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentWithLatestJob:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _document_response(db, document)


@router.get("/{document_id}/pages", response_model=list[DocumentPageRead])
def get_document_pages(document_id: str, db: Session = Depends(get_db)) -> list[DocumentPageRead]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    pages = db.scalars(
        select(DocumentPage).where(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number)
    ).all()
    return [DocumentPageRead.model_validate(page) for page in pages]


@router.get("/{document_id}/blocks", response_model=list[DocumentBlockRead])
def get_document_blocks(document_id: str, db: Session = Depends(get_db)) -> list[DocumentBlockRead]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    blocks = db.scalars(
        select(DocumentBlock)
        .where(DocumentBlock.document_id == document_id)
        .order_by(
            DocumentBlock.page_number.is_(None),
            DocumentBlock.page_number,
            DocumentBlock.created_at,
            DocumentBlock.id,
        )
    ).all()
    return [DocumentBlockRead.model_validate(block) for block in blocks]


@router.get("/{document_id}/tables", response_model=list[DocumentBlockRead])
def get_document_tables(document_id: str, db: Session = Depends(get_db)) -> list[DocumentBlockRead]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    blocks = db.scalars(
        select(DocumentBlock)
        .where(DocumentBlock.document_id == document_id, DocumentBlock.block_type == "table")
        .order_by(
            DocumentBlock.page_number.is_(None),
            DocumentBlock.page_number,
            DocumentBlock.created_at,
            DocumentBlock.id,
        )
    ).all()
    return [DocumentBlockRead.model_validate(block) for block in blocks]


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkRead])
def get_document_chunks(document_id: str, db: Session = Depends(get_db)) -> list[DocumentChunkRead]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    return [DocumentChunkRead.model_validate(chunk) for chunk in chunks]


@router.post("/{document_id}/estimate-ai-cost", response_model=AICostEstimateRead)
def estimate_document_ai_cost(document_id: str, db: Session = Depends(get_db)) -> AICostEstimateRead:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = _document_chunks_for_ai(db, document_id)
    return _ai_cost_estimate_response(document_id, chunks)


@router.post("/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
    queue: JobQueue = Depends(get_queue),
) -> UploadDocumentResponse:
    file_type = validate_upload_file(file)
    project = _get_or_create_default_project(db)
    document_id = str(uuid.uuid4())
    filename = sanitize_filename(file.filename or f"document.{file_type}")
    storage_key = f"documents/{project.id}/{document_id}/{filename}"
    mime_type = file.content_type or "application/octet-stream"

    storage.upload_fileobj(storage_key, file.file, mime_type)

    document = Document(
        id=document_id,
        project_id=project.id,
        filename=filename,
        original_filename=file.filename or filename,
        file_type=file_type,
        mime_type=mime_type,
        storage_key=storage_key,
        status=DocumentStatus.UPLOADED.value,
    )
    job = ExtractionJob(document_id=document.id, job_type=JobType.PARSE.value, status=JobStatus.QUEUED.value)
    db.add(document)
    db.add(job)
    db.commit()
    db.refresh(document)
    db.refresh(job)

    queue.push_job(job.id)

    return UploadDocumentResponse(
        document=DocumentWithLatestJob.model_validate(document),
        job=ExtractionJobRead.model_validate(job),
    )


@router.post("/{document_id}/extract", response_model=ExtractionJobRead, status_code=status.HTTP_201_CREATED)
def create_extraction_job(
    document_id: str,
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> ExtractionJobRead:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    job = ExtractionJob(document_id=document.id, job_type=JobType.PARSE.value, status=JobStatus.QUEUED.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    queue.push_job(job.id)
    return ExtractionJobRead.model_validate(job)


@router.post("/{document_id}/extract-ai", response_model=AIExtractionJobResponse, status_code=status.HTTP_201_CREATED)
def create_ai_extraction_job(
    document_id: str,
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> AIExtractionJobResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    _assert_ai_extraction_allowed(db)
    chunks = _document_chunks_for_ai(db, document_id)
    estimated_cost = _ai_cost_estimate_response(document_id, chunks)

    job = ExtractionJob(document_id=document.id, job_type=JobType.AI_EXTRACTION.value, status=JobStatus.QUEUED.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    queue.push_job(job.id)
    return AIExtractionJobResponse.model_validate(
        {
            "job": ExtractionJobRead.model_validate(job),
            "estimated_cost": estimated_cost,
        }
    )


@router.get("/{document_id}/extractions", response_model=DocumentExtractionsRead)
def get_document_extractions(document_id: str, db: Session = Depends(get_db)) -> DocumentExtractionsRead:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")

    chemical_entities = db.scalars(
        select(ChemicalEntity).where(ChemicalEntity.document_id == document_id).order_by(ChemicalEntity.created_at)
    ).all()
    reactions = db.scalars(
        select(ReactionRecord).where(ReactionRecord.document_id == document_id).order_by(ReactionRecord.created_at)
    ).all()
    measurements = db.scalars(
        select(MeasurementRecord)
        .where(MeasurementRecord.document_id == document_id)
        .order_by(MeasurementRecord.created_at)
    ).all()
    review_items = db.scalars(
        select(ReviewItem).where(ReviewItem.document_id == document_id).order_by(ReviewItem.created_at)
    ).all()

    return DocumentExtractionsRead.model_validate(
        {
            "chemical_entities": chemical_entities,
            "reactions": reactions,
            "measurements": measurements,
            "review_items": review_items,
        }
    )


@router.get("/{document_id}/review-items", response_model=list[ReviewItemRead])
def get_document_review_items(document_id: str, db: Session = Depends(get_db)) -> list[ReviewItemRead]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    review_items = db.scalars(
        select(ReviewItem).where(ReviewItem.document_id == document_id).order_by(ReviewItem.created_at, ReviewItem.id)
    ).all()
    return [ReviewItemRead.model_validate(item) for item in review_items]
