from __future__ import annotations

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.auth.permissions import (
    Permission,
    accessible_workspace_ids,
    require_workspace_permission,
)
from app.billing.enforcement import assert_can_create_project, assert_can_export, assert_can_upload_document
from app.database import get_db
from app.dependencies import get_queue, get_storage, get_webhook_delivery_queue
from app.developer_auth import (
    ApiActor,
    require_document_scope_and_permission,
    require_project_scope_and_permission,
    require_scope,
)
from app.document_upload import create_uploaded_document, file_size_bytes
from app.exports import create_download_url, run_export_job
from app.models import (
    ChemicalEntity,
    Document,
    DocumentChunk,
    ExportJob,
    ExtractionJob,
    MeasurementRecord,
    Project,
    ReactionRecord,
    ReviewItem,
)
from app.queue import JobQueue, WebhookDeliveryQueue
from app.routes.documents import (
    _ai_cost_estimate_response,
    _document_response,
    _latest_job,
    _queue_ai_extraction_job,
)
from app.schemas import (
    AICostEstimateRead,
    ChemicalEntityRead,
    CurrentMonthUsageRead,
    DocumentChunkRead,
    DocumentWithLatestJob,
    ExportJobCreateRequest,
    ExportJobRead,
    ExtractionJobRead,
    ProjectCreateRequest,
    ProjectRead,
    ReactionRecordRead,
    MeasurementRecordRead,
    V1DocumentCreateResponse,
    V1DocumentStatusResponse,
    V1EstimateResponse,
    V1ExtractRequest,
    V1ExtractResponse,
    V1RecordsResponse,
)
from app.storage import S3Storage, validate_upload_file
from app.usage import current_month_usage

router = APIRouter(prefix="/v1")


@router.get(
    "/projects",
    response_model=list[ProjectRead],
    tags=["v1-projects"],
    description="List projects accessible to the authenticated user or API key.",
)
def v1_list_projects(
    actor: ApiActor = Depends(require_scope("projects:read")),
    db: Session = Depends(get_db),
) -> list[ProjectRead]:
    projects = db.scalars(
        select(Project)
        .where(Project.id.in_(_accessible_project_ids(db, actor)))
        .order_by(Project.created_at.desc(), Project.id.desc())
    ).all()
    return [ProjectRead.model_validate(project) for project in projects]


@router.post(
    "/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    tags=["v1-projects"],
    description="Create a project in the user's account or an accessible workspace.",
)
def v1_create_project(
    payload: ProjectCreateRequest,
    actor: ApiActor = Depends(require_scope("projects:write")),
    db: Session = Depends(get_db),
) -> ProjectRead:
    name = payload.name.strip()
    if not name:
        raise _api_error(status.HTTP_400_BAD_REQUEST, "invalid_request", "Project name is required.")
    workspace_id = payload.resolved_workspace_id
    if actor.workspace_id:
        if workspace_id and workspace_id != actor.workspace_id:
            raise _api_error(status.HTTP_403_FORBIDDEN, "forbidden", "API key cannot access this workspace.")
        workspace_id = actor.workspace_id
    if workspace_id:
        access = require_workspace_permission(db, workspace_id, actor.user, Permission.CREATE_PROJECT)
        assert_can_create_project(db, access.workspace.owner, access.workspace)
        project = Project(user_id=actor.user_id, workspace_id=workspace_id, name=name)
    else:
        assert_can_create_project(db, actor.user)
        project = Project(user_id=actor.user_id, name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectRead,
    tags=["v1-projects"],
    description="Retrieve a project by id.",
)
def v1_get_project(
    project_id: str,
    actor: ApiActor = Depends(require_scope("projects:read")),
    db: Session = Depends(get_db),
) -> ProjectRead:
    access = require_project_scope_and_permission(
        db,
        actor,
        project_id,
        scope="projects:read",
        permission=Permission.VIEW,
    )
    return ProjectRead.model_validate(access.project)


@router.post(
    "/documents",
    response_model=V1DocumentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["v1-documents"],
    description="Upload a document. Files are stored in S3-compatible storage and a parse job is queued.",
)
async def v1_upload_document(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    auto_parse: bool = Form(default=True),
    auto_extract: bool = Form(default=False),
    actor: ApiActor = Depends(require_scope("documents:write")),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
    queue: JobQueue = Depends(get_queue),
    webhook_queue: WebhookDeliveryQueue = Depends(get_webhook_delivery_queue),
) -> V1DocumentCreateResponse:
    validate_upload_file(file)
    access = require_project_scope_and_permission(
        db,
        actor,
        project_id,
        scope="documents:write",
        permission=Permission.UPLOAD,
    )
    size_bytes = file_size_bytes(file)
    file.file.seek(0)
    assert_can_upload_document(db, access.billing_user, file_size_bytes=size_bytes, workspace=access.workspace)
    document, parse_job = create_uploaded_document(db, storage, queue, webhook_queue, file=file, project=access.project)
    _ = auto_parse
    extraction_job_id = None
    if auto_extract:
        if not actor.has_scope("extractions:write"):
            raise _api_error(
                status.HTTP_403_FORBIDDEN,
                "insufficient_scope",
                "API key requires scope: extractions:write.",
                {"required_scope": "extractions:write"},
            )
        response = _queue_ai_extraction_job(db, queue, document=document, current_user=actor.user, access=access)
        extraction_job_id = response.job.id
    return V1DocumentCreateResponse.model_validate(
        {
            "document_id": document.id,
            "filename": document.filename,
            "status": document.status,
            "parse_job_id": parse_job.id,
            "extraction_job_id": extraction_job_id,
        }
    )


@router.get(
    "/documents",
    response_model=list[DocumentWithLatestJob],
    tags=["v1-documents"],
    description="List documents accessible to the authenticated user or API key.",
)
def v1_list_documents(
    actor: ApiActor = Depends(require_scope("documents:read")),
    db: Session = Depends(get_db),
) -> list[DocumentWithLatestJob]:
    documents = db.scalars(
        select(Document)
        .where(Document.project_id.in_(_accessible_project_ids(db, actor)))
        .order_by(Document.created_at.desc(), Document.id.desc())
    ).all()
    return [_document_response(db, document) for document in documents]


@router.get(
    "/documents/{document_id}",
    response_model=DocumentWithLatestJob,
    tags=["v1-documents"],
    description="Retrieve document metadata and latest job status.",
)
def v1_get_document(
    document_id: str,
    actor: ApiActor = Depends(require_scope("documents:read")),
    db: Session = Depends(get_db),
) -> DocumentWithLatestJob:
    document, _ = require_document_scope_and_permission(
        db,
        actor,
        document_id,
        scope="documents:read",
        permission=Permission.VIEW,
    )
    return _document_response(db, document)


@router.get(
    "/documents/{document_id}/status",
    response_model=V1DocumentStatusResponse,
    tags=["v1-documents"],
    description="Retrieve a compact document status payload.",
)
def v1_get_document_status(
    document_id: str,
    actor: ApiActor = Depends(require_scope("documents:read")),
    db: Session = Depends(get_db),
) -> V1DocumentStatusResponse:
    document, _ = require_document_scope_and_permission(
        db,
        actor,
        document_id,
        scope="documents:read",
        permission=Permission.VIEW,
    )
    latest = _latest_job(db, document.id)
    return V1DocumentStatusResponse.model_validate(
        {
            "document_id": document.id,
            "status": document.status,
            "latest_job": ExtractionJobRead.model_validate(latest) if latest else None,
        }
    )


@router.get(
    "/documents/{document_id}/chunks",
    response_model=list[DocumentChunkRead],
    tags=["v1-documents"],
    description="List parsed chunks for a document.",
)
def v1_get_document_chunks(
    document_id: str,
    actor: ApiActor = Depends(require_scope("documents:read")),
    db: Session = Depends(get_db),
) -> list[DocumentChunkRead]:
    require_document_scope_and_permission(
        db,
        actor,
        document_id,
        scope="documents:read",
        permission=Permission.VIEW,
    )
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    return [DocumentChunkRead.model_validate(chunk) for chunk in chunks]


@router.post(
    "/documents/{document_id}/estimate",
    response_model=V1EstimateResponse,
    tags=["v1-extraction"],
    description="Estimate selected chunk count, tokens, and cost for AI extraction.",
)
def v1_estimate_document(
    document_id: str,
    actor: ApiActor = Depends(require_scope("extractions:read")),
    db: Session = Depends(get_db),
) -> V1EstimateResponse:
    require_document_scope_and_permission(
        db,
        actor,
        document_id,
        scope="extractions:read",
        permission=Permission.VIEW,
    )
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    estimate = _ai_cost_estimate_response(document_id, chunks)
    return _v1_estimate(estimate)


@router.post(
    "/documents/{document_id}/extract",
    response_model=V1ExtractResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["v1-extraction"],
    description="Queue AI structured extraction for a parsed document.",
)
def v1_extract_document(
    document_id: str,
    _: V1ExtractRequest | None = Body(default=None),
    actor: ApiActor = Depends(require_scope("extractions:write")),
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> V1ExtractResponse:
    document, access = require_document_scope_and_permission(
        db,
        actor,
        document_id,
        scope="extractions:write",
        permission=Permission.RUN_AI,
    )
    response = _queue_ai_extraction_job(db, queue, document=document, current_user=actor.user, access=access)
    return V1ExtractResponse.model_validate(
        {
            "job_id": response.job.id,
            "status": response.job.status,
            "estimated_cost_usd": response.estimated_cost.estimated_cost_usd,
        }
    )


@router.get(
    "/jobs/{job_id}",
    response_model=ExtractionJobRead,
    tags=["v1-extraction"],
    description="Retrieve an extraction or parsing job by id.",
)
def v1_get_job(
    job_id: str,
    actor: ApiActor = Depends(require_scope("extractions:read")),
    db: Session = Depends(get_db),
) -> ExtractionJobRead:
    job = db.get(ExtractionJob, job_id)
    if job is None:
        raise _api_error(status.HTTP_404_NOT_FOUND, "not_found", "Job not found.")
    require_document_scope_and_permission(
        db,
        actor,
        job.document_id,
        scope="extractions:read",
        permission=Permission.VIEW,
    )
    return ExtractionJobRead.model_validate(job)


@router.get(
    "/documents/{document_id}/records",
    response_model=V1RecordsResponse,
    tags=["v1-records"],
    description="Return extracted records for a document. Approved records are returned by default.",
)
def v1_get_document_records(
    document_id: str,
    include_unapproved: bool = False,
    actor: ApiActor = Depends(require_scope("records:read")),
    db: Session = Depends(get_db),
) -> V1RecordsResponse:
    require_document_scope_and_permission(
        db,
        actor,
        document_id,
        scope="records:read",
        permission=Permission.VIEW,
    )
    if include_unapproved and actor.type == "api_key" and not actor.has_scope("extractions:read"):
        raise _api_error(
            status.HTTP_403_FORBIDDEN,
            "insufficient_scope",
            "include_unapproved requires records:read and extractions:read scopes.",
            {"required_scope": "extractions:read"},
        )
    chemicals, reactions, measurements = _records_for_document(db, document_id, include_unapproved)
    return V1RecordsResponse.model_validate(
        {
            "document_id": document_id,
            "chemical_entities": [ChemicalEntityRead.model_validate(record) for record in chemicals],
            "reactions": [ReactionRecordRead.model_validate(record) for record in reactions],
            "measurements": [MeasurementRecordRead.model_validate(record) for record in measurements],
            "review_summary": _review_summary(db, document_id),
            "includes_unapproved": include_unapproved,
        }
    )


@router.get("/records/chemicals", tags=["v1-records"], description="List approved chemical entity records.")
def v1_list_chemical_records(
    actor: ApiActor = Depends(require_scope("records:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [_record_payload(record) for record in _query_records(db, actor, ChemicalEntity, "chemical_entity")]


@router.get("/records/reactions", tags=["v1-records"], description="List approved reaction records.")
def v1_list_reaction_records(
    actor: ApiActor = Depends(require_scope("records:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [_record_payload(record) for record in _query_records(db, actor, ReactionRecord, "reaction")]


@router.get("/records/measurements", tags=["v1-records"], description="List approved measurement records.")
def v1_list_measurement_records(
    actor: ApiActor = Depends(require_scope("records:read")),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [_record_payload(record) for record in _query_records(db, actor, MeasurementRecord, "measurement")]


@router.get(
    "/search",
    tags=["v1-search"],
    description="Search approved scientific records with evidence previews.",
)
def v1_search(
    q: str = "",
    actor: ApiActor = Depends(require_scope("records:read")),
    db: Session = Depends(get_db),
) -> dict:
    query = q.strip()
    if not query:
        return {"query": query, "result_count": 0, "records": []}
    like = f"%{query}%"
    project_ids = _accessible_project_ids(db, actor)
    if not project_ids:
        return {"query": query, "result_count": 0, "records": []}
    document_ids = db.scalars(select(Document.id).where(Document.project_id.in_(project_ids))).all()
    records: list[dict] = []
    for model, record_type, fields in (
        (ChemicalEntity, "chemical_entity", [ChemicalEntity.name, ChemicalEntity.normalized_name, ChemicalEntity.role]),
        (ReactionRecord, "reaction", [ReactionRecord.reaction_name, ReactionRecord.raw_yield_value]),
        (MeasurementRecord, "measurement", [MeasurementRecord.measurement_type, MeasurementRecord.subject]),
    ):
        conditions = [field.ilike(like) for field in fields]
        matches = (
            db.scalars(
                select(model)
                .join(ReviewItem, ReviewItem.record_id == model.id)
                .where(
                    model.document_id.in_(document_ids),
                    ReviewItem.record_type == record_type,
                    ReviewItem.status == "approved",
                    or_(*conditions),
                )
                .limit(50)
            )
            .unique()
            .all()
        )
        records.extend({"record_type": record_type, **_record_payload(match)} for match in matches)
    return {"query": query, "result_count": len(records), "records": records[:100]}


@router.post(
    "/exports",
    response_model=ExportJobRead,
    status_code=status.HTTP_201_CREATED,
    tags=["v1-exports"],
    description="Create an export job. Exports are scoped to approved records by default.",
)
def v1_create_export(
    payload: ExportJobCreateRequest,
    actor: ApiActor = Depends(require_scope("exports:write")),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
    webhook_queue: WebhookDeliveryQueue = Depends(get_webhook_delivery_queue),
) -> ExportJobRead:
    access = require_project_scope_and_permission(
        db,
        actor,
        payload.project_id,
        scope="exports:write",
        permission=Permission.EXPORT,
    )
    assert_can_export(db, access.billing_user)
    job = ExportJob(project_id=access.project.id, export_format=payload.export_format.strip() or "json")
    db.add(job)
    db.flush()
    run_export_job(db, storage, job, webhook_queue=webhook_queue)
    db.commit()
    db.refresh(job)
    return _export_job_response(job, storage)


@router.get("/exports", response_model=list[ExportJobRead], tags=["v1-exports"], description="List export jobs.")
def v1_list_exports(
    actor: ApiActor = Depends(require_scope("exports:read")),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
) -> list[ExportJobRead]:
    jobs = db.scalars(
        select(ExportJob)
        .join(Project, ExportJob.project_id == Project.id)
        .where(Project.id.in_(_accessible_project_ids(db, actor)))
        .order_by(ExportJob.created_at.desc(), ExportJob.id.desc())
        .limit(50)
    ).all()
    return [_export_job_response(job, storage) for job in jobs]


@router.get("/exports/{export_id}", response_model=ExportJobRead, tags=["v1-exports"], description="Get an export job.")
def v1_get_export(
    export_id: str,
    actor: ApiActor = Depends(require_scope("exports:read")),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
) -> ExportJobRead:
    job = _get_accessible_export(db, actor, export_id)
    return _export_job_response(job, storage)


@router.get(
    "/exports/{export_id}/download",
    tags=["v1-exports"],
    description="Return download metadata for an export job.",
)
def v1_download_export(
    export_id: str,
    actor: ApiActor = Depends(require_scope("exports:read")),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
) -> dict:
    job = _get_accessible_export(db, actor, export_id)
    if not job.storage_key:
        raise _api_error(status.HTTP_404_NOT_FOUND, "not_found", "Export file is not ready for download.")
    return {
        "export_id": job.id,
        "status": job.status,
        "storage_key": job.storage_key,
        "download_url": create_download_url(storage, job.storage_key),
    }


@router.get("/usage", response_model=CurrentMonthUsageRead, tags=["v1-usage"], description="Get current-month usage.")
def v1_usage(
    actor: ApiActor = Depends(require_scope("projects:read")),
    db: Session = Depends(get_db),
) -> CurrentMonthUsageRead:
    # Reuse the existing usage shape for developer integrations.
    usage = current_month_usage(db, actor.user)
    return CurrentMonthUsageRead.model_validate({**usage.__dict__, "recent_records": []})


def _accessible_project_ids(db: Session, actor: ApiActor) -> list[str]:
    workspace_ids = accessible_workspace_ids(db, actor.user)
    if actor.workspace_id:
        if actor.workspace_id not in workspace_ids:
            raise _api_error(status.HTTP_403_FORBIDDEN, "forbidden", "API key cannot access this workspace.")
        return db.scalars(select(Project.id).where(Project.workspace_id == actor.workspace_id)).all()
    filters = [and_(Project.user_id == actor.user_id, Project.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(Project.workspace_id.in_(workspace_ids))
    return db.scalars(select(Project.id).where(or_(*filters))).all()


def _v1_estimate(estimate: AICostEstimateRead) -> V1EstimateResponse:
    return V1EstimateResponse.model_validate(
        {
            "document_id": estimate.document_id,
            "model": estimate.model,
            "selected_chunks": estimate.selected_chunks,
            "estimated_input_tokens": estimate.estimated_input_tokens,
            "estimated_output_tokens": estimate.estimated_output_tokens,
            "estimated_cost_usd": estimate.estimated_cost_usd,
        }
    )


def _records_for_document(
    db: Session,
    document_id: str,
    include_unapproved: bool,
) -> tuple[list[ChemicalEntity], list[ReactionRecord], list[MeasurementRecord]]:
    if include_unapproved:
        rejected = db.scalars(
            select(ReviewItem.record_id).where(ReviewItem.document_id == document_id, ReviewItem.status == "rejected")
        ).all()
        return (
            db.scalars(
                select(ChemicalEntity).where(ChemicalEntity.document_id == document_id, ChemicalEntity.id.not_in(rejected))
            ).all(),
            db.scalars(
                select(ReactionRecord).where(ReactionRecord.document_id == document_id, ReactionRecord.id.not_in(rejected))
            ).all(),
            db.scalars(
                select(MeasurementRecord).where(
                    MeasurementRecord.document_id == document_id,
                    MeasurementRecord.id.not_in(rejected),
                )
            ).all(),
        )
    return (
        _approved_records(db, document_id, ChemicalEntity, "chemical_entity"),
        _approved_records(db, document_id, ReactionRecord, "reaction"),
        _approved_records(db, document_id, MeasurementRecord, "measurement"),
    )


def _approved_records(db: Session, document_id: str, model, record_type: str) -> list:
    return db.scalars(
        select(model)
        .join(ReviewItem, ReviewItem.record_id == model.id)
        .where(
            model.document_id == document_id,
            ReviewItem.document_id == document_id,
            ReviewItem.record_type == record_type,
            ReviewItem.status == "approved",
        )
        .order_by(model.created_at.desc(), model.id.desc())
    ).all()


def _query_records(db: Session, actor: ApiActor, model, record_type: str) -> list:
    project_ids = _accessible_project_ids(db, actor)
    if not project_ids:
        return []
    document_ids = db.scalars(select(Document.id).where(Document.project_id.in_(project_ids))).all()
    if not document_ids:
        return []
    return db.scalars(
        select(model)
        .join(ReviewItem, ReviewItem.record_id == model.id)
        .where(
            model.document_id.in_(document_ids),
            ReviewItem.record_type == record_type,
            ReviewItem.status == "approved",
        )
        .order_by(model.created_at.desc(), model.id.desc())
        .limit(100)
    ).all()


def _review_summary(db: Session, document_id: str) -> dict[str, int]:
    rows = db.execute(
        select(ReviewItem.status, func.count(ReviewItem.id))
        .where(ReviewItem.document_id == document_id)
        .group_by(ReviewItem.status)
    ).all()
    summary = {"pending": 0, "approved": 0, "needs_review": 0, "rejected": 0}
    summary.update({status_value: count for status_value, count in rows})
    return summary


def _record_payload(record) -> dict:
    return {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
        if column.name not in {"storage_key"}
    }


def _get_accessible_export(db: Session, actor: ApiActor, export_id: str) -> ExportJob:
    job = db.get(ExportJob, export_id)
    if job is None:
        raise _api_error(status.HTTP_404_NOT_FOUND, "not_found", "Export not found.")
    require_project_scope_and_permission(
        db,
        actor,
        job.project_id,
        scope="exports:read",
        permission=Permission.EXPORT,
    )
    return job


def _export_job_response(job: ExportJob, storage: S3Storage) -> ExportJobRead:
    return ExportJobRead.model_validate(job).model_copy(
        update={"download_url": create_download_url(storage, job.storage_key)}
    )


def _api_error(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message, "details": details or {}})
