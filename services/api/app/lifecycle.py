from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete, or_, select, update
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.models import (
    AiUsageRecord,
    ApiKey,
    ApiRequestLog,
    AuditLog,
    BatchJob,
    BatchJobItem,
    BillingEvent,
    ChemicalEntity,
    ContactMessage,
    Document,
    DocumentBlock,
    DocumentChunk,
    DocumentPage,
    ExportJob,
    ExtractionJob,
    ExtractionRun,
    MeasurementRecord,
    Project,
    ReactionRecord,
    ReviewItem,
    Subscription,
    User,
    UserAiSettings,
    WebhookDelivery,
    WebhookEndpoint,
    Workspace,
    WorkspaceMember,
)
from app.storage import S3Storage


SENSITIVE_COLUMNS = {"password_hash", "encrypted_openai_api_key", "key_hash", "encrypted_secret"}


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _row_json(row: Any) -> dict[str, Any]:
    return {
        column.key: _json_value(getattr(row, column.key))
        for column in inspect(row).mapper.column_attrs
        if column.key not in SENSITIVE_COLUMNS
    }


def _rows(db: Session, model: Any, predicate: Any) -> list[Any]:
    return list(db.scalars(select(model).where(predicate)).all())


def build_user_lifecycle_export(db: Session, email: str) -> dict[str, Any]:
    user = db.scalars(select(User).where(User.email == email)).first()
    contact_messages = _rows(db, ContactMessage, ContactMessage.email == email)
    if user is None:
        return {"user": None, "contactMessages": [_row_json(row) for row in contact_messages], "contentIncluded": False}

    workspace_ids = list(db.scalars(select(Workspace.id).where(Workspace.owner_user_id == user.id)).all())
    project_predicate = Project.user_id == user.id
    if workspace_ids:
        project_predicate = or_(project_predicate, Project.workspace_id.in_(workspace_ids))
    projects = _rows(db, Project, project_predicate)
    project_ids = [row.id for row in projects]
    documents = _rows(db, Document, Document.project_id.in_(project_ids)) if project_ids else []
    document_ids = [row.id for row in documents]
    extraction_jobs = _rows(db, ExtractionJob, ExtractionJob.document_id.in_(document_ids)) if document_ids else []
    extraction_job_ids = [row.id for row in extraction_jobs]

    def serialized(model: Any, predicate: Any) -> list[dict[str, Any]]:
        return [_row_json(row) for row in _rows(db, model, predicate)]

    data: dict[str, Any] = {
        "user": _row_json(user),
        "workspaces": serialized(Workspace, Workspace.id.in_(workspace_ids)) if workspace_ids else [],
        "workspaceMemberships": serialized(
            WorkspaceMember,
            or_(WorkspaceMember.user_id == user.id, WorkspaceMember.invited_email == email),
        ),
        "projects": [_row_json(row) for row in projects],
        "documents": [_row_json(row) for row in documents],
        "extractionJobs": [_row_json(row) for row in extraction_jobs],
        "userAiSettings": serialized(UserAiSettings, UserAiSettings.user_id == user.id),
        "apiKeys": serialized(ApiKey, ApiKey.user_id == user.id),
        "apiRequestLogs": serialized(ApiRequestLog, ApiRequestLog.user_id == user.id),
        "usage": serialized(AiUsageRecord, AiUsageRecord.user_id == user.id),
        "batchJobs": serialized(BatchJob, BatchJob.user_id == user.id),
        "subscriptions": serialized(Subscription, Subscription.user_id == user.id),
        "billingEvents": serialized(BillingEvent, BillingEvent.user_id == user.id),
        "auditLogs": serialized(
            AuditLog,
            or_(AuditLog.actor_user_id == user.id, AuditLog.target_user_id == user.id),
        ),
        "contactMessages": [_row_json(row) for row in contact_messages],
        "webhookEndpoints": serialized(WebhookEndpoint, WebhookEndpoint.user_id == user.id),
        "contentIncluded": False,
    }
    if document_ids:
        for key, model in (
            ("documentPages", DocumentPage),
            ("documentBlocks", DocumentBlock),
            ("documentChunks", DocumentChunk),
            ("chemicalEntities", ChemicalEntity),
            ("reactions", ReactionRecord),
            ("measurements", MeasurementRecord),
            ("reviewItems", ReviewItem),
        ):
            data[key] = serialized(model, model.document_id.in_(document_ids))
    if extraction_job_ids:
        data["extractionRuns"] = serialized(ExtractionRun, ExtractionRun.job_id.in_(extraction_job_ids))
    data["objectInventory"] = [
        {"type": "document", "id": row.id, "storageKey": row.storage_key, "sizeBytes": row.file_size_bytes}
        for row in documents
    ]
    return data


def delete_user_lifecycle_data(db: Session, storage: S3Storage, email: str) -> dict[str, Any]:
    user = db.scalars(select(User).where(User.email == email)).first()
    if user is None:
        result = db.execute(delete(ContactMessage).where(ContactMessage.email == email))
        db.commit()
        return {"userDeleted": False, "recordsAlreadyAbsent": True, "contactMessagesDeleted": result.rowcount or 0}

    owned_workspace_ids = list(db.scalars(select(Workspace.id).where(Workspace.owner_user_id == user.id)).all())
    if owned_workspace_ids:
        other_member = db.scalars(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id.in_(owned_workspace_ids),
                WorkspaceMember.user_id.is_not(None),
                WorkspaceMember.user_id != user.id,
            )
        ).first()
        if other_member is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Owned workspaces with other members must be transferred before account deletion.",
            )

    active_subscription = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status.not_in(("free", "canceled", "cancelled", "expired")),
        )
    ).first()
    if active_subscription is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active Extract billing must be canceled before account deletion.",
        )

    project_predicate = Project.user_id == user.id
    if owned_workspace_ids:
        project_predicate = or_(project_predicate, Project.workspace_id.in_(owned_workspace_ids))
    project_ids = list(db.scalars(select(Project.id).where(project_predicate)).all())
    document_ids = list(db.scalars(select(Document.id).where(Document.project_id.in_(project_ids))).all()) if project_ids else []
    extraction_job_ids = list(
        db.scalars(select(ExtractionJob.id).where(ExtractionJob.document_id.in_(document_ids))).all()
    ) if document_ids else []
    batch_job_predicate = BatchJob.user_id == user.id
    if project_ids:
        batch_job_predicate = or_(batch_job_predicate, BatchJob.project_id.in_(project_ids))
    batch_job_ids = list(db.scalars(select(BatchJob.id).where(batch_job_predicate)).all())

    storage_keys: set[str] = set()
    if document_ids:
        storage_keys.update(db.scalars(select(Document.storage_key).where(Document.id.in_(document_ids))).all())
        storage_keys.update(
            key for key in db.scalars(select(DocumentPage.image_key).where(DocumentPage.document_id.in_(document_ids))).all() if key
        )
    if project_ids:
        storage_keys.update(
            key for key in db.scalars(select(ExportJob.storage_key).where(ExportJob.project_id.in_(project_ids))).all() if key
        )
    for key in storage_keys:
        storage.delete_file(key)

    deleted = 0

    def remove(model: Any, predicate: Any) -> None:
        nonlocal deleted
        result = db.execute(delete(model).where(predicate))
        deleted += result.rowcount or 0

    if document_ids:
        remove(AiUsageRecord, AiUsageRecord.document_id.in_(document_ids))
        remove(BatchJobItem, BatchJobItem.document_id.in_(document_ids))
        for model in (DocumentPage, DocumentBlock, DocumentChunk, ChemicalEntity, ReactionRecord, MeasurementRecord, ReviewItem):
            remove(model, model.document_id.in_(document_ids))
    if extraction_job_ids:
        remove(ExtractionRun, ExtractionRun.job_id.in_(extraction_job_ids))
        remove(BatchJobItem, BatchJobItem.extraction_job_id.in_(extraction_job_ids))
        remove(ExtractionJob, ExtractionJob.id.in_(extraction_job_ids))
    if batch_job_ids:
        remove(BatchJobItem, BatchJobItem.batch_job_id.in_(batch_job_ids))
        remove(AiUsageRecord, AiUsageRecord.batch_job_id.in_(batch_job_ids))
        remove(BatchJob, BatchJob.id.in_(batch_job_ids))
    if document_ids:
        remove(Document, Document.id.in_(document_ids))
    if project_ids:
        remove(AiUsageRecord, AiUsageRecord.project_id.in_(project_ids))
        remove(ExportJob, ExportJob.project_id.in_(project_ids))
        remove(Project, Project.id.in_(project_ids))

    endpoint_ids = list(db.scalars(select(WebhookEndpoint.id).where(WebhookEndpoint.user_id == user.id)).all())
    if endpoint_ids:
        remove(WebhookDelivery, WebhookDelivery.webhook_endpoint_id.in_(endpoint_ids))
    remove(ApiRequestLog, ApiRequestLog.user_id == user.id)
    remove(ApiKey, ApiKey.user_id == user.id)
    remove(WebhookEndpoint, WebhookEndpoint.user_id == user.id)
    remove(UserAiSettings, UserAiSettings.user_id == user.id)
    remove(AiUsageRecord, AiUsageRecord.user_id == user.id)
    remove(Subscription, Subscription.user_id == user.id)
    remove(BillingEvent, BillingEvent.user_id == user.id)
    remove(AuditLog, or_(AuditLog.actor_user_id == user.id, AuditLog.target_user_id == user.id))
    remove(ContactMessage, ContactMessage.email == email)
    remove(WorkspaceMember, or_(WorkspaceMember.user_id == user.id, WorkspaceMember.invited_email == email))
    db.execute(update(WorkspaceMember).where(WorkspaceMember.invited_by_user_id == user.id).values(invited_by_user_id=None))
    if owned_workspace_ids:
        remove(ApiRequestLog, ApiRequestLog.workspace_id.in_(owned_workspace_ids))
        remove(ApiKey, ApiKey.workspace_id.in_(owned_workspace_ids))
        workspace_endpoint_ids = list(
            db.scalars(select(WebhookEndpoint.id).where(WebhookEndpoint.workspace_id.in_(owned_workspace_ids))).all()
        )
        if workspace_endpoint_ids:
            remove(WebhookDelivery, WebhookDelivery.webhook_endpoint_id.in_(workspace_endpoint_ids))
        remove(WebhookEndpoint, WebhookEndpoint.workspace_id.in_(owned_workspace_ids))
        remove(WorkspaceMember, WorkspaceMember.workspace_id.in_(owned_workspace_ids))
        remove(Workspace, Workspace.id.in_(owned_workspace_ids))
    remove(User, User.id == user.id)
    db.commit()
    return {"userDeleted": True, "recordsDeleted": deleted, "objectsDeleted": len(storage_keys)}
