import redis

from app.config import Settings


class JobQueue:
    def __init__(self, settings: Settings) -> None:
        self.queue_name = settings.redis_queue
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    def push_job(self, job_id: str) -> None:
        self.redis.rpush(self.queue_name, job_id)

    def pop_job(self, timeout_seconds: int = 5) -> str | None:
        result = self.redis.blpop(self.queue_name, timeout=timeout_seconds)
        if result is None:
            return None
        _, job_id = result
        return job_id
