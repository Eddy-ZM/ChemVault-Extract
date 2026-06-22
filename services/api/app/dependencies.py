from functools import lru_cache

from app.config import get_settings
from app.queue import JobQueue
from app.storage import S3Storage


@lru_cache
def _storage_client() -> S3Storage:
    return S3Storage(get_settings())


@lru_cache
def _job_queue() -> JobQueue:
    return JobQueue(get_settings())


def get_storage() -> S3Storage:
    return _storage_client()


def get_queue() -> JobQueue:
    return _job_queue()
