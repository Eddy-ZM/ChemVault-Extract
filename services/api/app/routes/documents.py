import uuid

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.ai_settings import build_ai_settings_for_user, user_uses_own_openai_key
from app.auth.permissions import (
    Permission,
    ProjectAccess,
    accessible_workspace_ids,
    document_project_access,
    project_access,
    require_document_permission,
    require_project_permission,
)
from app.billing.enforcement import (
    assert_can_batch_extract,
    assert_can_batch_upload,
    assert_can_create_project,
    assert_can_run_ai_extraction,
    assert_can_upload_document,
)
from app.config import get_settings
from app.config import Settings
from app.config.ai import AI_COST_WARNING, estimate_ai_cost_for_chunks, get_ai_settings
from app.constants import BatchJobItemStatus, BatchJobStatus, BatchJobType, DocumentStatus, JobStatus, JobType
from app.database import get_db
from app.dependencies import get_queue, get_storage, get_webhook_delivery_queue
from app.document_upload import create_uploaded_document, file_size_bytes
from app.models import (
    BatchJob,
    BatchJobItem,
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
from app.extractors.pipeline import normalize_records_for_job
from app.queue import JobQueue, WebhookDeliveryQueue
from app.schemas import (
    AICostEstimateRead,
    AIExtractionJobResponse,
    BatchAIExtractionRequest,
    BatchAIExtractionResponse,
    BatchUploadResponse,
    DocumentBlockRead,
    DocumentChunkRead,
    DocumentExtractionsRead,
    NormalizeResponse,
    NormalizationRequest,
    NormalizedRecordsRead,
    DocumentPageRead,
    DocumentWithLatestJob,
    ExtractionJobRead,
    ReviewItemRead,
    UploadDocumentResponse,
)
from app.security import get_current_user
from app.storage import S3Storage, sanitize_filename, validate_upload_file
from app.webhook_delivery import enqueue_webhook_event_for_document
from app.usage import create_ai_usage_record

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


def _get_or_create_default_project(db: Session, user: User) -> Project:
    settings = get_settings()
    project = db.scalars(
        select(Project).where(
            Project.user_id == user.id,
            Project.workspace_id.is_(None),
            Project.name == settings.default_project_name,
        )
    ).first()
    if project is None:
        assert_can_create_project(db, user)
        project = Project(user_id=user.id, name=settings.default_project_name)
        db.add(project)
        db.flush()
    return project


def _file_size_bytes(file: UploadFile) -> int:
    return file_size_bytes(file)


def _owned_document(db: Session, document_id: str, user: User) -> Document:
    document, _ = require_document_permission(db, document_id, user, Permission.VIEW)
    return document


def _document_chunks_for_ai(db: Session, document_id: str) -> list[DocumentChunk]:
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    return chunks


def _empty_ai_cost_estimate(document_id: str, settings: Settings, ai_settings=None) -> AICostEstimateRead:
    ai_settings = ai_settings or get_ai_settings(settings)
    warning = f"{AI_COST_WARNING} Parse has not completed; this is a pre-parse estimate."
    model_name = ai_settings.default_model
    return AICostEstimateRead.model_validate(
        {
            "document_id": document_id,
            "selected_chunks": 0,
            "selected_chunk_ids": [],
            "estimated_input_tokens": 0,
            "estimated_output_tokens": 0,
            "model": model_name,
            "estimated_cost_usd": 0.0,
            "warning": warning,
        }
    )


def _ai_cost_estimate_response(document_id: str, chunks: list[DocumentChunk], ai_settings=None) -> AICostEstimateRead:
    settings = get_settings()
    ai_settings = ai_settings or get_ai_settings(settings)
    if not chunks:
        return _empty_ai_cost_estimate(document_id=document_id, settings=settings, ai_settings=ai_settings)
    estimate = estimate_ai_cost_for_chunks(document_id=document_id, chunks=chunks, ai_settings=ai_settings)
    return AICostEstimateRead.model_validate(
        {
            "document_id": estimate.document_id,
            "selected_chunks": estimate.selected_chunks,
            "selected_chunk_ids": estimate.selected_chunk_ids,
            "estimated_input_tokens": estimate.estimated_input_tokens,
            "estimated_output_tokens": estimate.estimated_output_tokens,
            "model": estimate.model,
            "estimated_cost_usd": estimate.estimated_cost_usd,
            "warning": estimate.warning,
        }
    )


def _queue_ai_extraction_job(
    db: Session,
    queue: JobQueue,
    *,
    document: Document,
    current_user: User,
    access: ProjectAccess | None = None,
    batch_job_id: str | None = None,
) -> AIExtractionJobResponse:
    access = access or project_access(db, document.project_id, current_user)
    if not access.can(Permission.RUN_AI):
        raise HTTPException(status_code=403, detail="Project role cannot run_ai.")
    chunks = _document_chunks_for_ai(db, document.id)
    ai_settings = build_ai_settings_for_user(db, current_user, get_settings(), include_api_key=False)
    estimated_cost = _ai_cost_estimate_response(document.id, chunks, ai_settings)
    try:
        build_ai_settings_for_user(db, current_user, get_settings(), include_api_key=True)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    used_own_api_key = user_uses_own_openai_key(db, current_user, get_settings())
    assert_can_run_ai_extraction(
        db,
        access.billing_user,
        estimated_cost_usd=estimated_cost.estimated_cost_usd,
        counts_platform_cost=not used_own_api_key,
        workspace=access.workspace,
    )

    job = ExtractionJob(document_id=document.id, job_type=JobType.AI_EXTRACTION.value, status=JobStatus.QUEUED.value)
    db.add(job)
    db.flush()
    create_ai_usage_record(
        db,
        user=current_user,
        document=document,
        job=job,
        provider=ai_settings.provider,
        model=estimated_cost.model,
        input_tokens_estimated=estimated_cost.estimated_input_tokens,
        output_tokens_estimated=estimated_cost.estimated_output_tokens,
        estimated_cost_usd=estimated_cost.estimated_cost_usd,
        used_own_api_key=used_own_api_key,
        usage_user=access.billing_user,
        workspace_id=access.workspace_id,
        batch_job_id=batch_job_id,
    )
    db.commit()
    db.refresh(job)
    queue.push_job(job.id)
    return AIExtractionJobResponse.model_validate(
        {
            "job": ExtractionJobRead.model_validate(job),
            "estimated_cost": estimated_cost,
        }
    )


@router.get("", response_model=list[DocumentWithLatestJob])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentWithLatestJob]:
    workspace_ids = accessible_workspace_ids(db, current_user)
    filters = [and_(Project.user_id == current_user.id, Project.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(Project.workspace_id.in_(workspace_ids))
    documents = db.scalars(
        select(Document)
        .join(Project, Document.project_id == Project.id)
        .where(or_(*filters))
        .order_by(Document.created_at.desc(), Document.id.desc())
    ).all()
    return [_document_response(db, document) for document in documents]


@router.get("/{document_id}", response_model=DocumentWithLatestJob)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentWithLatestJob:
    document = _owned_document(db, document_id, current_user)
    return _document_response(db, document)


@router.get("/{document_id}/pages", response_model=list[DocumentPageRead])
def get_document_pages(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentPageRead]:
    _owned_document(db, document_id, current_user)
    pages = db.scalars(
        select(DocumentPage).where(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number)
    ).all()
    return [DocumentPageRead.model_validate(page) for page in pages]


@router.get("/{document_id}/blocks", response_model=list[DocumentBlockRead])
def get_document_blocks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentBlockRead]:
    _owned_document(db, document_id, current_user)
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
def get_document_tables(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentBlockRead]:
    _owned_document(db, document_id, current_user)
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
def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentChunkRead]:
    _owned_document(db, document_id, current_user)
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    return [DocumentChunkRead.model_validate(chunk) for chunk in chunks]


@router.post("/{document_id}/estimate-ai-cost", response_model=AICostEstimateRead)
def estimate_document_ai_cost(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AICostEstimateRead:
    _owned_document(db, document_id, current_user)
    chunks = _document_chunks_for_ai(db, document_id)
    ai_settings = build_ai_settings_for_user(db, current_user, get_settings(), include_api_key=False)
    return _ai_cost_estimate_response(document_id, chunks, ai_settings)


@router.post("/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
    queue: JobQueue = Depends(get_queue),
    webhook_queue: WebhookDeliveryQueue = Depends(get_webhook_delivery_queue),
) -> UploadDocumentResponse:
    file_type = validate_upload_file(file)
    file_size_bytes = _file_size_bytes(file)
    file.file.seek(0)
    if project_id:
        access = require_project_permission(db, project_id, current_user, Permission.UPLOAD)
        assert_can_upload_document(
            db,
            access.billing_user,
            file_size_bytes=file_size_bytes,
            workspace=access.workspace,
        )
        project = access.project
    else:
        assert_can_upload_document(db, current_user, file_size_bytes=file_size_bytes)
        project = _get_or_create_default_project(db, current_user)
    document, job = create_uploaded_document(db, storage, queue, webhook_queue, file=file, project=project)

    return UploadDocumentResponse(
        document=DocumentWithLatestJob.model_validate(document),
        job=ExtractionJobRead.model_validate(job),
    )


@router.post("/batch-upload", response_model=BatchUploadResponse, status_code=status.HTTP_201_CREATED)
async def batch_upload_documents(
    project_id: str = Form(...),
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
    queue: JobQueue = Depends(get_queue),
    webhook_queue: WebhookDeliveryQueue = Depends(get_webhook_delivery_queue),
) -> BatchUploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")
    access = require_project_permission(db, project_id, current_user, Permission.UPLOAD)

    prepared: list[tuple[UploadFile, str, int]] = []
    total_size = 0
    for file in files:
        file_type = validate_upload_file(file)
        file_size_bytes = _file_size_bytes(file)
        file.file.seek(0)
        prepared.append((file, file_type, file_size_bytes))
        total_size += file_size_bytes

    assert_can_batch_upload(
        db,
        access.billing_user,
        total_file_size_bytes=total_size,
        file_count=len(prepared),
        workspace=access.workspace,
    )

    batch = BatchJob(
        project_id=access.project.id,
        workspace_id=access.workspace_id,
        user_id=current_user.id,
        type=BatchJobType.UPLOAD_PARSE.value,
        status=BatchJobStatus.QUEUED.value,
        total_items=len(prepared),
        progress=0.0,
    )
    db.add(batch)
    db.flush()

    documents: list[Document] = []
    jobs: list[ExtractionJob] = []
    for file, file_type, file_size_bytes in prepared:
        document_id = str(uuid.uuid4())
        filename = sanitize_filename(file.filename or f"document.{file_type}")
        storage_key = f"documents/{access.project.id}/{document_id}/{filename}"
        mime_type = file.content_type or "application/octet-stream"
        file.file.seek(0)
        storage.upload_fileobj(storage_key, file.file, mime_type)

        document = Document(
            id=document_id,
            project_id=access.project.id,
            filename=filename,
            original_filename=file.filename or filename,
            file_type=file_type,
            mime_type=mime_type,
            storage_key=storage_key,
            file_size_bytes=file_size_bytes,
            status=DocumentStatus.UPLOADED.value,
        )
        job = ExtractionJob(document_id=document.id, job_type=JobType.PARSE.value, status=JobStatus.QUEUED.value)
        db.add(document)
        db.add(job)
        db.flush()
        db.add(
            BatchJobItem(
                batch_job_id=batch.id,
                document_id=document.id,
                extraction_job_id=job.id,
                status=BatchJobItemStatus.QUEUED.value,
            )
        )
        jobs.append(job)
        documents.append(document)

    db.commit()
    for job in jobs:
        queue.push_job(job.id)
    for document, job in zip(documents, jobs, strict=True):
        enqueue_webhook_event_for_document(
            db,
            webhook_queue,
            document=document,
            event_type="document.uploaded",
            data={
                "filename": document.filename,
                "file_type": document.file_type,
                "status": document.status,
                "parse_job_id": job.id,
                "document_url": f"/v1/documents/{document.id}",
            },
        )
    db.commit()

    return BatchUploadResponse.model_validate(
        {
            "batch_job_id": batch.id,
            "documents": len(jobs),
            "jobs": [ExtractionJobRead.model_validate(job) for job in jobs],
        }
    )


@router.post("/{document_id}/extract", response_model=ExtractionJobRead, status_code=status.HTTP_201_CREATED)
def create_extraction_job(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> ExtractionJobRead:
    document, _ = require_document_permission(db, document_id, current_user, Permission.RUN_AI)

    job = ExtractionJob(document_id=document.id, job_type=JobType.PARSE.value, status=JobStatus.QUEUED.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    queue.push_job(job.id)
    return ExtractionJobRead.model_validate(job)


@router.post("/{document_id}/extract-ai", response_model=AIExtractionJobResponse, status_code=status.HTTP_201_CREATED)
def create_ai_extraction_job(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> AIExtractionJobResponse:
    document, access = require_document_permission(db, document_id, current_user, Permission.RUN_AI)
    return _queue_ai_extraction_job(db, queue, document=document, current_user=current_user, access=access)


@router.post("/batch-extract-ai", response_model=BatchAIExtractionResponse, status_code=status.HTTP_201_CREATED)
def create_batch_ai_extraction_jobs(
    payload: BatchAIExtractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> BatchAIExtractionResponse:
    if not payload.document_ids:
        raise HTTPException(status_code=400, detail="documentIds is required.")
    if len(payload.document_ids) > 50:
        raise HTTPException(status_code=400, detail="Batch extraction is limited to 50 documents per request.")

    responses: list[AIExtractionJobResponse] = []
    for document_id in payload.document_ids:
        document, access = require_document_permission(db, document_id, current_user, Permission.BATCH_EXTRACT)
        assert_can_batch_extract(db, access.billing_user, access.workspace)
        responses.append(_queue_ai_extraction_job(db, queue, document=document, current_user=current_user, access=access))
    return BatchAIExtractionResponse.model_validate({"jobs": responses})


@router.get("/{document_id}/extractions", response_model=DocumentExtractionsRead)
def get_document_extractions(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentExtractionsRead:
    _owned_document(db, document_id, current_user)

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
def get_document_review_items(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReviewItemRead]:
    require_document_permission(db, document_id, current_user, Permission.VIEW)
    review_items = db.scalars(
        select(ReviewItem).where(ReviewItem.document_id == document_id).order_by(ReviewItem.created_at, ReviewItem.id)
    ).all()
    return [ReviewItemRead.model_validate(item) for item in review_items]


@router.post("/{document_id}/normalize", response_model=NormalizeResponse, status_code=status.HTTP_201_CREATED)
def normalize_document_records(
    document_id: str,
    payload: NormalizationRequest | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    webhook_queue: WebhookDeliveryQueue = Depends(get_webhook_delivery_queue),
) -> NormalizeResponse:
    document, _ = require_document_permission(db, document_id, current_user, Permission.REVIEW)

    review_items = normalize_records_for_job(
        db,
        None,
        document_id=document_id,
        raw_data=payload.raw_data if payload else None,
    )
    db.commit()
    enqueue_webhook_event_for_document(
        db,
        webhook_queue,
        document=document,
        event_type="normalization.completed",
        data={"review_items_updated": len(review_items), "review_url": f"/documents/{document.id}/review"},
    )
    db.commit()

    return NormalizeResponse.model_validate(
        {
            "status": "completed",
            "updated_records": len(review_items),
            "review_items": review_items,
        }
    )


@router.get("/{document_id}/normalized-records", response_model=NormalizedRecordsRead)
def get_normalized_records(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NormalizedRecordsRead:
    require_document_permission(db, document_id, current_user, Permission.VIEW)

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

    return NormalizedRecordsRead.model_validate(
        {
            "chemical_entities": chemical_entities,
            "reactions": reactions,
            "measurements": measurements,
        }
    )
