from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import BatchJobItemStatus, BatchJobStatus
from app.models import BatchJob, BatchJobItem
from app.webhook_delivery import enqueue_webhook_event


def set_batch_item_status(
    db: Session,
    *,
    extraction_job_id: str,
    status: str,
    error: str | None = None,
) -> None:
    items = db.scalars(
        select(BatchJobItem).where(BatchJobItem.extraction_job_id == extraction_job_id)
    ).all()
    for item in items:
        item.status = status
        item.error = error
        if status in {BatchJobItemStatus.COMPLETED.value, BatchJobItemStatus.FAILED.value, BatchJobItemStatus.SKIPPED.value}:
            item.completed_at = datetime.now(timezone.utc)
        item.batch_job.status = BatchJobStatus.RUNNING.value
        recalculate_batch_job(db, item.batch_job_id)


def recalculate_batch_job(db: Session, batch_job_id: str) -> BatchJob | None:
    batch = db.get(BatchJob, batch_job_id)
    if batch is None:
        return None
    previous_status = batch.status

    counts = dict(
        db.execute(
            select(BatchJobItem.status, func.count(BatchJobItem.id))
            .where(BatchJobItem.batch_job_id == batch_job_id)
            .group_by(BatchJobItem.status)
        ).all()
    )
    total = batch.total_items or sum(int(value) for value in counts.values())
    completed = int(counts.get(BatchJobItemStatus.COMPLETED.value, 0))
    failed = int(counts.get(BatchJobItemStatus.FAILED.value, 0))
    skipped = int(counts.get(BatchJobItemStatus.SKIPPED.value, 0))
    running = int(counts.get(BatchJobItemStatus.RUNNING.value, 0))
    queued = int(counts.get(BatchJobItemStatus.QUEUED.value, 0))
    done = completed + failed + skipped

    batch.total_items = total
    batch.completed_items = completed
    batch.failed_items = failed
    batch.progress = round((done / total) * 100, 2) if total else 100.0

    if total == 0:
        batch.status = BatchJobStatus.COMPLETED.value
        batch.completed_at = datetime.now(timezone.utc)
    elif queued == total and batch.status not in {BatchJobStatus.CANCELLED.value}:
        batch.status = BatchJobStatus.QUEUED.value
    elif done >= total:
        if batch.status == BatchJobStatus.CANCELLED.value and skipped > 0:
            batch.status = BatchJobStatus.CANCELLED.value
        elif failed >= total:
            batch.status = BatchJobStatus.FAILED.value
        elif failed > 0:
            batch.status = BatchJobStatus.PARTIAL_FAILED.value
        else:
            batch.status = BatchJobStatus.COMPLETED.value
        batch.completed_at = datetime.now(timezone.utc)
    elif running > 0 or queued > 0:
        if batch.status != BatchJobStatus.CANCELLED.value:
            batch.status = BatchJobStatus.RUNNING.value
    if batch.status != previous_status and batch.status in {
        BatchJobStatus.COMPLETED.value,
        BatchJobStatus.PARTIAL_FAILED.value,
        BatchJobStatus.FAILED.value,
    }:
        event_type = {
            BatchJobStatus.COMPLETED.value: "batch.completed",
            BatchJobStatus.PARTIAL_FAILED.value: "batch.partial_failed",
            BatchJobStatus.FAILED.value: "batch.failed",
        }[batch.status]
        enqueue_webhook_event(
            db,
            None,
            event_type=event_type,
            user_id=batch.user_id,
            workspace_id=batch.workspace_id,
            project_id=batch.project_id,
            data={
                "batch_job_id": batch.id,
                "status": batch.status,
                "total_items": batch.total_items,
                "completed_items": batch.completed_items,
                "failed_items": batch.failed_items,
            },
        )
    return batch


def cancel_queued_items(db: Session, batch: BatchJob) -> BatchJob:
    for item in batch.items:
        if item.status == BatchJobItemStatus.QUEUED.value:
            item.status = BatchJobItemStatus.SKIPPED.value
            item.error = "Cancelled before processing."
            item.completed_at = datetime.now(timezone.utc)
    batch.status = BatchJobStatus.CANCELLED.value
    recalculate_batch_job(db, batch.id)
    return batch
