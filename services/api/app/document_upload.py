from __future__ import annotations

import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.constants import DocumentStatus, JobStatus, JobType
from app.models import Document, ExtractionJob, Project
from app.queue import JobQueue, WebhookDeliveryQueue
from app.storage import S3Storage, sanitize_filename, validate_upload_file
from app.webhook_delivery import enqueue_webhook_event_for_document


def file_size_bytes(file: UploadFile) -> int:
    try:
        current = file.file.tell()
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(current)
        return int(size)
    except (AttributeError, OSError):
        return 0


def create_uploaded_document(
    db: Session,
    storage: S3Storage,
    queue: JobQueue,
    webhook_queue: WebhookDeliveryQueue | None = None,
    *,
    file: UploadFile,
    project: Project,
) -> tuple[Document, ExtractionJob]:
    file_type = validate_upload_file(file)
    size_bytes = file_size_bytes(file)
    file.file.seek(0)
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
        file_size_bytes=size_bytes,
        status=DocumentStatus.UPLOADED.value,
    )
    job = ExtractionJob(document_id=document.id, job_type=JobType.PARSE.value, status=JobStatus.QUEUED.value)
    db.add(document)
    db.add(job)
    db.commit()
    db.refresh(document)
    db.refresh(job)
    queue.push_job(job.id)
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
    return document, job
