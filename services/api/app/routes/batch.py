from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.ai_settings import build_ai_settings_for_user, user_uses_own_openai_key
from app.auth.permissions import (
    Permission,
    accessible_workspace_ids,
    project_access,
    require_document_permission,
    require_project_permission,
)
from app.batch_jobs import cancel_queued_items, recalculate_batch_job
from app.billing.enforcement import assert_can_batch_extract, assert_can_run_ai_extraction
from app.config import get_settings
from app.config.ai import estimate_ai_cost_for_chunks
from app.constants import BatchJobItemStatus, BatchJobStatus, BatchJobType, JobStatus, JobType
from app.database import get_db
from app.dependencies import get_queue
from app.models import BatchJob, BatchJobItem, Document, DocumentChunk, ExtractionJob, Project, User
from app.queue import JobQueue
from app.schemas import (
    BatchExtractAIRequest,
    BatchExtractAIResponse,
    BatchJobDetailRead,
    BatchJobRead,
)
from app.security import get_current_user
from app.usage import create_ai_usage_record

router = APIRouter(prefix="/batch", tags=["batch"])


@router.get("/jobs", response_model=list[BatchJobRead])
def list_batch_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BatchJobRead]:
    workspace_ids = accessible_workspace_ids(db, current_user)
    filters = [and_(Project.user_id == current_user.id, Project.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(Project.workspace_id.in_(workspace_ids))
    jobs = db.scalars(
        select(BatchJob)
        .join(Project, BatchJob.project_id == Project.id)
        .where(or_(*filters))
        .order_by(BatchJob.created_at.desc(), BatchJob.id.desc())
        .limit(100)
    ).all()
    return [BatchJobRead.model_validate(job) for job in jobs]


@router.get("/jobs/{batch_job_id}", response_model=BatchJobDetailRead)
def get_batch_job(
    batch_job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchJobDetailRead:
    batch = _batch_or_404(db, batch_job_id)
    project_access(db, batch.project_id, current_user)
    recalculate_batch_job(db, batch.id)
    db.commit()
    db.refresh(batch)
    return BatchJobDetailRead.model_validate(batch)


@router.post("/jobs/{batch_job_id}/cancel", response_model=BatchJobDetailRead)
def cancel_batch_job(
    batch_job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchJobDetailRead:
    batch = _batch_or_404(db, batch_job_id)
    _require_batch_mutation_permission(db, batch, current_user)
    cancel_queued_items(db, batch)
    db.commit()
    db.refresh(batch)
    return BatchJobDetailRead.model_validate(batch)


@router.post("/jobs/{batch_job_id}/retry-failed", response_model=BatchJobDetailRead)
def retry_failed_batch_items(
    batch_job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> BatchJobDetailRead:
    batch = _batch_or_404(db, batch_job_id)
    access = _require_batch_mutation_permission(db, batch, current_user)
    failed_items = [item for item in batch.items if item.status == BatchJobItemStatus.FAILED.value and item.document_id]
    if not failed_items:
        raise HTTPException(status_code=400, detail="No failed batch items to retry.")

    if batch.type == BatchJobType.AI_EXTRACTION.value:
        estimates = [_estimate_document_cost(db, item.document_id, current_user) for item in failed_items if item.document_id]
        total_cost = sum(item["estimated_cost_usd"] for item in estimates)
        used_own_api_key = user_uses_own_openai_key(db, current_user, get_settings())
        assert_can_run_ai_extraction(
            db,
            access.billing_user,
            estimated_cost_usd=total_cost,
            counts_platform_cost=not used_own_api_key,
            file_count=len(estimates),
            workspace=access.workspace,
        )

    retry_job_ids: list[str] = []
    for item in failed_items:
        job_type = JobType.AI_EXTRACTION.value if batch.type == BatchJobType.AI_EXTRACTION.value else JobType.PARSE.value
        job = ExtractionJob(document_id=item.document_id, job_type=job_type, status=JobStatus.QUEUED.value)
        db.add(job)
        db.flush()
        item.extraction_job_id = job.id
        item.status = BatchJobItemStatus.QUEUED.value
        item.error = None
        item.completed_at = None
        if batch.type == BatchJobType.AI_EXTRACTION.value:
            estimate = _estimate_document_cost(db, item.document_id, current_user)
            used_own_api_key = user_uses_own_openai_key(db, current_user, get_settings())
            create_ai_usage_record(
                db,
                user=current_user,
                usage_user=access.billing_user,
                document=db.get(Document, item.document_id),
                job=job,
                provider=estimate["provider"],
                model=estimate["model"],
                input_tokens_estimated=estimate["estimated_input_tokens"],
                output_tokens_estimated=estimate["estimated_output_tokens"],
                estimated_cost_usd=estimate["estimated_cost_usd"],
                used_own_api_key=used_own_api_key,
                workspace_id=access.workspace_id,
                batch_job_id=batch.id,
            )
        retry_job_ids.append(job.id)

    batch.status = BatchJobStatus.QUEUED.value
    recalculate_batch_job(db, batch.id)
    db.commit()
    for job_id in retry_job_ids:
        queue.push_job(job_id)
    db.refresh(batch)
    return BatchJobDetailRead.model_validate(batch)


@router.post("/extract-ai", response_model=BatchExtractAIResponse, status_code=status.HTTP_201_CREATED)
def create_batch_ai_extraction(
    payload: BatchExtractAIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> BatchExtractAIResponse:
    project_id = payload.resolved_project_id
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required.")
    access = require_project_permission(db, project_id, current_user, Permission.BATCH_EXTRACT)
    assert_can_batch_extract(db, access.billing_user, access.workspace)
    _assert_ai_key_available(db, current_user)

    documents = _resolve_batch_documents(db, access.project.id, payload, current_user)
    if not documents:
        raise HTTPException(status_code=400, detail="No documents selected for batch extraction.")
    if len(documents) > 100:
        raise HTTPException(status_code=400, detail="Batch extraction is limited to 100 documents per request.")

    estimates = [_estimate_document_cost(db, document.id, current_user) for document in documents]
    total_cost = round(sum(item["estimated_cost_usd"] for item in estimates), 6)
    total_input = sum(item["estimated_input_tokens"] for item in estimates)
    total_output = sum(item["estimated_output_tokens"] for item in estimates)
    used_own_api_key = user_uses_own_openai_key(db, current_user, get_settings())
    assert_can_run_ai_extraction(
        db,
        access.billing_user,
        estimated_cost_usd=total_cost,
        counts_platform_cost=not used_own_api_key,
        file_count=len(documents),
        workspace=access.workspace,
    )

    batch = BatchJob(
        project_id=access.project.id,
        workspace_id=access.workspace_id,
        user_id=current_user.id,
        type=BatchJobType.AI_EXTRACTION.value,
        status=BatchJobStatus.QUEUED.value,
        total_items=len(documents),
        progress=0.0,
        estimated_total_cost_usd=total_cost,
        estimated_input_tokens=total_input,
        estimated_output_tokens=total_output,
    )
    db.add(batch)
    db.flush()

    job_ids: list[str] = []
    for document, estimate in zip(documents, estimates, strict=True):
        job = ExtractionJob(document_id=document.id, job_type=JobType.AI_EXTRACTION.value, status=JobStatus.QUEUED.value)
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
        create_ai_usage_record(
            db,
            user=current_user,
            usage_user=access.billing_user,
            document=document,
            job=job,
            provider=estimate["provider"],
            model=estimate["model"],
            input_tokens_estimated=estimate["estimated_input_tokens"],
            output_tokens_estimated=estimate["estimated_output_tokens"],
            estimated_cost_usd=estimate["estimated_cost_usd"],
            used_own_api_key=used_own_api_key,
            workspace_id=access.workspace_id,
            batch_job_id=batch.id,
        )
        job_ids.append(job.id)

    db.commit()
    for job_id in job_ids:
        queue.push_job(job_id)
    db.refresh(batch)
    return BatchExtractAIResponse.model_validate(
        {
            "batch_job_id": batch.id,
            "documents": len(documents),
            "estimated_total_cost_usd": total_cost,
            "estimated_input_tokens": total_input,
            "estimated_output_tokens": total_output,
            "batch_job": BatchJobRead.model_validate(batch),
        }
    )


def _resolve_batch_documents(
    db: Session,
    project_id: str,
    payload: BatchExtractAIRequest,
    current_user: User,
) -> list[Document]:
    mode = payload.mode.strip().lower()
    if mode in {"all_unprocessed", "all_unprocessed_documents"}:
        ai_job_exists = (
            select(ExtractionJob.id)
            .where(
                ExtractionJob.document_id == Document.id,
                ExtractionJob.job_type == JobType.AI_EXTRACTION.value,
            )
            .exists()
        )
        documents = db.scalars(
            select(Document)
            .where(Document.project_id == project_id, ~ai_job_exists)
            .order_by(Document.created_at, Document.id)
        ).all()
    else:
        if mode not in {"selected", "selected_documents"}:
            raise HTTPException(status_code=400, detail="Unsupported batch extraction mode.")
        document_ids = payload.resolved_document_ids
        if not document_ids:
            raise HTTPException(status_code=400, detail="document_ids is required for selected_documents mode.")
        documents = db.scalars(
            select(Document).where(Document.project_id == project_id, Document.id.in_(document_ids))
        ).all()
        found_ids = {document.id for document in documents}
        missing = [document_id for document_id in document_ids if document_id not in found_ids]
        if missing:
            raise HTTPException(status_code=404, detail=f"Documents not found in project: {', '.join(missing)}")
    for document in documents:
        require_document_permission(db, document.id, current_user, Permission.BATCH_EXTRACT)
    return documents


def _estimate_document_cost(db: Session, document_id: str, user: User) -> dict:
    settings = get_settings()
    ai_settings = build_ai_settings_for_user(db, user, settings, include_api_key=False)
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    if chunks:
        estimate = estimate_ai_cost_for_chunks(document_id=document_id, chunks=chunks, ai_settings=ai_settings)
        return {
            "provider": ai_settings.provider,
            "model": estimate.model,
            "estimated_input_tokens": estimate.estimated_input_tokens,
            "estimated_output_tokens": estimate.estimated_output_tokens,
            "estimated_cost_usd": estimate.estimated_cost_usd,
        }
    return {
        "provider": ai_settings.provider,
        "model": ai_settings.default_model,
        "estimated_input_tokens": 0,
        "estimated_output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def _assert_ai_key_available(db: Session, user: User) -> None:
    try:
        build_ai_settings_for_user(db, user, get_settings(), include_api_key=True)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _batch_or_404(db: Session, batch_job_id: str) -> BatchJob:
    batch = db.get(BatchJob, batch_job_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    return batch


def _require_batch_mutation_permission(db: Session, batch: BatchJob, user: User):
    permission = Permission.BATCH_EXTRACT if batch.type == BatchJobType.AI_EXTRACTION.value else Permission.UPLOAD
    return require_project_permission(db, batch.project_id, user, permission)
