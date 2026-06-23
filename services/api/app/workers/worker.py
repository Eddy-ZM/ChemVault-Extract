import logging
import tempfile
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.batch_jobs import set_batch_item_status
from app.chunking import build_chunks
from app.config import get_settings
from app.constants import DocumentStatus, JobStatus, JobType
from app.constants import BatchJobItemStatus
from app.database import SessionLocal
from app.extractors import normalize_records_for_job, run_structured_extraction
from app.models import DocumentBlock, DocumentChunk, DocumentPage, ExtractionJob, ExtractionRun
from app.parsers.interface import ParsedBlock, ParsedDocument
from app.parsers.registry import parse_document
from app.queue import JobQueue, WebhookDeliveryQueue
from app.storage import S3Storage
from app.usage import mark_ai_usage_completed, mark_ai_usage_failed
from app.webhook_delivery import (
    deliver_webhook_delivery,
    enqueue_due_webhook_deliveries,
    enqueue_webhook_event_for_document,
)

logger = logging.getLogger("chemvault.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _record_status(db: Session, job: ExtractionJob, status: JobStatus, message: str | None = None) -> None:
    job.status = status.value
    if status == JobStatus.REVIEW_READY:
        job.document.status = DocumentStatus.REVIEW_READY.value
    elif status == JobStatus.FAILED:
        job.document.status = DocumentStatus.FAILED.value
    db.add(ExtractionRun(job_id=job.id, status=status.value, message=message))
    db.commit()
    db.refresh(job)


def _persist_parsed_document(db: Session, job: ExtractionJob, parsed: ParsedDocument, max_chunk_words: int) -> None:
    db.query(DocumentPage).filter(DocumentPage.document_id == job.document_id).delete()
    db.query(DocumentBlock).filter(DocumentBlock.document_id == job.document_id).delete()
    db.query(DocumentChunk).filter(DocumentChunk.document_id == job.document_id).delete()
    db.flush()

    for page in parsed.pages:
        db.add(
            DocumentPage(
                document_id=job.document_id,
                page_number=page.page_number,
                text=page.text,
                width=page.width,
                height=page.height,
                metadata_=page.metadata,
            )
        )

    parsed_blocks = list(parsed.blocks)
    for index, table in enumerate(parsed.tables):
        has_matching_table_block = any(
            block.block_type == "table"
            and block.page_number == table.page_number
            and block.html == table.html
            and ((block.metadata or {}).get("sheet_name") == (table.metadata or {}).get("sheet_name"))
            for block in parsed_blocks
        )
        if not has_matching_table_block:
            parsed_blocks.append(
                ParsedBlock(
                    block_type="table",
                    text=table.csv_text,
                    page_number=table.page_number,
                    section=table.section,
                    html=table.html,
                    metadata={**(table.metadata or {}), "rows": table.rows or []},
                )
            )

    for block in parsed_blocks:
        db.add(
            DocumentBlock(
                document_id=job.document_id,
                page_number=block.page_number,
                block_type=block.block_type,
                section=block.section,
                text=block.text,
                html=block.html,
                bbox=block.bbox,
                metadata_=block.metadata,
            )
        )

    chunks = build_chunks(parsed_blocks, max_tokens=max_chunk_words)
    for chunk in chunks:
        db.add(
            DocumentChunk(
                document_id=job.document_id,
                chunk_index=chunk.chunk_index,
                section=chunk.section,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                text=chunk.text,
                token_count=chunk.token_count,
            )
        )

    job.document.status = DocumentStatus.PARSED.value
    db.commit()
    db.refresh(job)


def _parse_job_document(db: Session, job: ExtractionJob, storage_client: S3Storage, max_chunk_words: int) -> None:
    suffix = Path(job.document.filename).suffix or f".{job.document.file_type}"
    with tempfile.NamedTemporaryFile(suffix=suffix) as temp_file:
        storage_client.download_file(job.document.storage_key, temp_file.name)
        parsed = parse_document(temp_file.name, job.document.mime_type)
    if parsed.errors:
        raise RuntimeError("; ".join(parsed.errors))
    _persist_parsed_document(db, job, parsed, max_chunk_words)


def _document_has_chunks(db: Session, document_id: str) -> bool:
    return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).first() is not None


def _process_parse_job(
    db: Session,
    job: ExtractionJob,
    storage_client: S3Storage,
    step_delay_seconds: float,
    max_chunk_words: int,
) -> None:
    _record_status(db, job, JobStatus.PARSING)
    _parse_job_document(db, job, storage_client, max_chunk_words)
    time.sleep(step_delay_seconds)
    _record_status(db, job, JobStatus.REVIEW_READY)
    enqueue_webhook_event_for_document(
        db,
        None,
        document=job.document,
        event_type="document.parsed",
        data={
            "job_id": job.id,
            "status": job.status,
            "pages_url": f"/v1/documents/{job.document_id}",
            "chunks_url": f"/v1/documents/{job.document_id}/chunks",
        },
    )
    db.commit()


def _process_ai_extraction_job(
    db: Session,
    job: ExtractionJob,
    storage_client: S3Storage,
    step_delay_seconds: float,
    max_chunk_words: int,
) -> None:
    settings = get_settings()
    if not _document_has_chunks(db, job.document_id):
        _record_status(db, job, JobStatus.PARSING)
        _parse_job_document(db, job, storage_client, max_chunk_words)
        enqueue_webhook_event_for_document(
            db,
            None,
            document=job.document,
            event_type="document.parsed",
            data={
                "job_id": job.id,
                "status": job.status,
                "chunks_url": f"/v1/documents/{job.document_id}/chunks",
            },
        )
        db.commit()

    _record_status(db, job, JobStatus.EXTRACTING)
    enqueue_webhook_event_for_document(
        db,
        None,
        document=job.document,
        event_type="extraction.started",
        data={"job_id": job.id, "status": job.status},
    )
    db.commit()
    run_structured_extraction(db, job, settings)
    _record_status(db, job, JobStatus.VALIDATING)

    _record_status(db, job, JobStatus.NORMALIZING)
    try:
        normalize_records_for_job(db, job.id)
        enqueue_webhook_event_for_document(
            db,
            None,
            document=job.document,
            event_type="normalization.completed",
            data={"job_id": job.id, "status": job.status},
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Normalization failed for job %s: %s", job.id, exc)
        enqueue_webhook_event_for_document(
            db,
            None,
            document=job.document,
            event_type="normalization.failed",
            data={"job_id": job.id, "error": str(exc)},
        )
        db.commit()

    time.sleep(step_delay_seconds)
    _record_status(db, job, JobStatus.REVIEW_READY)
    mark_ai_usage_completed(db, job.id)
    enqueue_webhook_event_for_document(
        db,
        None,
        document=job.document,
        event_type="extraction.completed",
        data={
            "job_id": job.id,
            "status": job.status,
            "records_url": f"/v1/documents/{job.document_id}/records",
            "review_url": f"/documents/{job.document_id}/review",
        },
    )
    db.commit()


def process_job(
    job_id: str,
    storage: S3Storage | None = None,
    step_delay_seconds: float | None = None,
    webhook_queue: WebhookDeliveryQueue | None = None,
) -> None:
    settings = get_settings()
    storage_client = storage or S3Storage(settings)
    delay = settings.worker_step_delay_seconds if step_delay_seconds is None else step_delay_seconds
    with SessionLocal() as db:
        job = db.get(ExtractionJob, job_id)
        if job is None:
            logger.warning("Skipping missing job %s", job_id)
            return
        if any(item.status == BatchJobItemStatus.SKIPPED.value for item in job.batch_items):
            logger.info("Skipping cancelled batch item job %s", job_id)
            return

        try:
            set_batch_item_status(db, extraction_job_id=job.id, status=BatchJobItemStatus.RUNNING.value)
            db.commit()
            job.error = None
            if (job.job_type or JobType.PARSE.value) == JobType.AI_EXTRACTION.value:
                _process_ai_extraction_job(db, job, storage_client, delay, settings.max_chunk_tokens)
            else:
                _process_parse_job(db, job, storage_client, delay, settings.max_chunk_tokens)
            set_batch_item_status(db, extraction_job_id=job.id, status=BatchJobItemStatus.COMPLETED.value)
            db.commit()
            logger.info("Job %s reached %s", job.id, JobStatus.REVIEW_READY.value)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            job = db.get(ExtractionJob, job_id)
            if job is not None:
                job.error = str(exc)
                _record_status(db, job, JobStatus.FAILED, str(exc))
                if (job.job_type or JobType.PARSE.value) == JobType.AI_EXTRACTION.value:
                    mark_ai_usage_failed(db, job.id)
                    event_type = "extraction.failed"
                else:
                    event_type = "document.parse_failed"
                enqueue_webhook_event_for_document(
                    db,
                    webhook_queue,
                    document=job.document,
                    event_type=event_type,
                    data={"job_id": job.id, "error": str(exc), "status": job.status},
                )
                set_batch_item_status(
                    db,
                    extraction_job_id=job.id,
                    status=BatchJobItemStatus.FAILED.value,
                    error=str(exc),
                )
                db.commit()
            logger.exception("Job %s failed", job_id)


def run() -> None:
    settings = get_settings()
    queue = JobQueue(settings)
    webhook_queue = WebhookDeliveryQueue(settings)
    logger.info("Worker listening on Redis queue %s", settings.redis_queue)
    while True:
        with SessionLocal() as db:
            enqueue_due_webhook_deliveries(db, webhook_queue)
            db.commit()
        delivery_id = webhook_queue.pop_delivery(timeout_seconds=1)
        if delivery_id is not None:
            with SessionLocal() as db:
                deliver_webhook_delivery(db, delivery_id)
            continue
        job_id = queue.pop_job(timeout_seconds=5)
        if job_id is None:
            continue
        process_job(job_id, webhook_queue=webhook_queue)


if __name__ == "__main__":
    run()
