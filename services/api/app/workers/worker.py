import logging
import tempfile
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.chunking import build_chunks
from app.config import get_settings
from app.constants import DocumentStatus, JobStatus
from app.database import SessionLocal
from app.models import DocumentBlock, DocumentChunk, DocumentPage, ExtractionJob, ExtractionRun
from app.parsers.interface import ParsedBlock
from app.parsers.registry import parse_document
from app.queue import JobQueue
from app.storage import S3Storage

logger = logging.getLogger("chemvault.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _record_status(db: Session, job: ExtractionJob, status: JobStatus, message: str | None = None) -> None:
    job.status = status.value
    if status == JobStatus.REVIEW_READY:
        if job.document.status != DocumentStatus.PARSED.value:
            job.document.status = DocumentStatus.REVIEW_READY.value
    elif status == JobStatus.FAILED:
        job.document.status = DocumentStatus.FAILED.value
    db.add(ExtractionRun(job_id=job.id, status=status.value, message=message))
    db.commit()
    db.refresh(job)


def _replace_parsed_records(db: Session, job: ExtractionJob, local_path: str) -> None:
    parsed = parse_document(local_path, job.document.mime_type)
    if parsed.errors:
        raise RuntimeError("; ".join(parsed.errors))

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
            )
        )

    parsed_blocks = list(parsed.blocks)
    for table in parsed.tables:
        if not any(
            block.block_type == "table"
            and block.page_number == table.page_number
            and block.html == table.html
            and block.text == table.csv_text
            for block in parsed_blocks
        ):
            parsed_blocks.append(
                ParsedBlock(
                    block_type="table",
                    page_number=table.page_number,
                    section=table.section,
                    text=table.csv_text,
                    html=table.html,
                    metadata=table.metadata,
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
    db.commit()


def _save_chunks(db: Session, job: ExtractionJob, max_tokens: int) -> None:
    rows = (
        db.query(DocumentBlock)
        .filter(DocumentBlock.document_id == job.document_id)
        .order_by(DocumentBlock.page_number.is_(None), DocumentBlock.page_number, DocumentBlock.created_at, DocumentBlock.id)
        .all()
    )
    parsed_blocks = [
        ParsedBlock(
            block_type=row.block_type,
            page_number=row.page_number,
            section=row.section,
            text=row.text,
            html=row.html,
            bbox=row.bbox,
            metadata=row.metadata_,
        )
        for row in rows
    ]
    chunks = build_chunks(parsed_blocks, max_tokens=max_tokens)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == job.document_id).delete()
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


def process_job(job_id: str, storage: S3Storage | None = None, step_delay_seconds: float | None = None) -> None:
    settings = get_settings()
    storage_client = storage or S3Storage(settings)
    delay = settings.worker_step_delay_seconds if step_delay_seconds is None else step_delay_seconds
    with SessionLocal() as db:
        job = db.get(ExtractionJob, job_id)
        if job is None:
            logger.warning("Skipping missing job %s", job_id)
            return

        try:
            _record_status(db, job, JobStatus.PARSING)
            suffix = Path(job.document.filename).suffix or f".{job.document.file_type}"
            with tempfile.NamedTemporaryFile(suffix=suffix) as temp_file:
                storage_client.download_file(job.document.storage_key, temp_file.name)
                _replace_parsed_records(db, job, temp_file.name)

            time.sleep(delay)
            _record_status(db, job, JobStatus.CHUNKING)
            _save_chunks(db, job, settings.max_chunk_tokens)
            time.sleep(delay)
            _record_status(db, job, JobStatus.REVIEW_READY)
            logger.info("Job %s reached %s", job.id, JobStatus.REVIEW_READY.value)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            job = db.get(ExtractionJob, job_id)
            if job is not None:
                job.error = str(exc)
                _record_status(db, job, JobStatus.FAILED, str(exc))
            logger.exception("Job %s failed", job_id)


def run() -> None:
    settings = get_settings()
    queue = JobQueue(settings)
    logger.info("Worker listening on Redis queue %s", settings.redis_queue)
    while True:
        job_id = queue.pop_job(timeout_seconds=5)
        if job_id is None:
            continue
        process_job(job_id)


if __name__ == "__main__":
    run()
