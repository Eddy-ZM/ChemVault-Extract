from __future__ import annotations

import redis

from app.config import Settings


class RedisQueue:
    def __init__(self, settings: Settings, queue_name: str) -> None:
        self.queue_name = queue_name
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    def push(self, message: str) -> None:
        self.redis.rpush(self.queue_name, message)

    def pop(self, timeout_seconds: int = 5) -> str | None:
        result = self.redis.blpop(self.queue_name, timeout=timeout_seconds)
        if result is None:
            return None
        _, message = result
        return message
