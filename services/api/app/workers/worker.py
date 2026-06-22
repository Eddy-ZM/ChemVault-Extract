import logging
import time

from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import DocumentStatus, JobStatus
from app.database import SessionLocal
from app.models import ExtractionJob, ExtractionRun
from app.queue import JobQueue
from app.storage import S3Storage

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


def process_job(job_id: str, storage: S3Storage | None = None, step_delay_seconds: float | None = None) -> None:
    settings = get_settings()
    _ = storage
    delay = settings.worker_step_delay_seconds if step_delay_seconds is None else step_delay_seconds
    with SessionLocal() as db:
        job = db.get(ExtractionJob, job_id)
        if job is None:
            logger.warning("Skipping missing job %s", job_id)
            return

        try:
            _record_status(db, job, JobStatus.PARSING)
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
