from __future__ import annotations

from app.config import Settings
from app.queue.base import QueueBackend
from app.queue.cloudflare_queue import CloudflareQueue
from app.queue.redis_queue import RedisQueue


class JobQueue:
    def __init__(self, settings: Settings) -> None:
        self.backend = _build_backend(settings, settings.redis_queue)

    def push_job(self, job_id: str) -> None:
        self.backend.push(job_id)

    def pop_job(self, timeout_seconds: int = 5) -> str | None:
        return self.backend.pop(timeout_seconds)


class WebhookDeliveryQueue:
    def __init__(self, settings: Settings) -> None:
        self.backend = _build_backend(settings, settings.webhook_delivery_queue)

    def push_delivery(self, delivery_id: str) -> None:
        self.backend.push(delivery_id)

    def pop_delivery(self, timeout_seconds: int = 1) -> str | None:
        return self.backend.pop(timeout_seconds)


def _build_backend(settings: Settings, queue_name: str) -> QueueBackend:
    provider = settings.queue_provider.lower().strip()
    if provider == "redis":
        return RedisQueue(settings, queue_name)
    if provider == "cloudflare":
        return CloudflareQueue(settings, queue_name)
    raise RuntimeError(f"Unsupported QUEUE_PROVIDER: {settings.queue_provider}")
