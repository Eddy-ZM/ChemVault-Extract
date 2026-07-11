from __future__ import annotations

import time
from typing import Any

import redis
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.billing.plans import get_effective_plan, get_plan_limits
from app.config import get_settings

RATE_LIMITS = {
    "free": {"per_minute": 60, "per_day": 1000},
    "student": {"per_minute": 120, "per_day": 5000},
    "researcher": {"per_minute": 300, "per_day": 20000},
    "lab": {"per_minute": 600, "per_day": 100000},
    "admin": {"per_minute": 5000, "per_day": 1000000},
}

_redis_client: redis.Redis | None = None
_fallback_counts: dict[str, tuple[int, int]] = {}


def get_actor_rate_limit(actor: Any) -> dict[str, int]:
    plan = get_effective_plan(actor.user)
    limits = RATE_LIMITS.get(plan, RATE_LIMITS["free"])
    # Keep this call as a guard that unknown plans still resolve through billing config.
    get_plan_limits(plan)
    return limits


def enforce_rate_limit(actor: Any, _: Session) -> None:
    limits = get_actor_rate_limit(actor)
    identity = f"api_key:{actor.api_key_id}" if actor.api_key_id else f"user:{actor.user_id}"
    now = _now_seconds()
    minute_key = f"chemvault:api-rate:{identity}:m:{int(now // 60)}"
    day_key = f"chemvault:api-rate:{identity}:d:{int(now // 86400)}"

    try:
        minute_count, day_count = _increment_redis(minute_key, day_key)
    except Exception:
        minute_count, day_count = _increment_fallback(minute_key, day_key)

    if minute_count > limits["per_minute"] or day_count > limits["per_day"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "rate_limit_exceeded",
                "message": "Rate limit exceeded. Please try again later.",
                "details": {
                    "per_minute": limits["per_minute"],
                    "per_day": limits["per_day"],
                },
            },
        )


def _increment_redis(minute_key: str, day_key: str) -> tuple[int, int]:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
            socket_connect_timeout=0.1,
            socket_timeout=0.1,
        )
    pipe = _redis_client.pipeline()
    pipe.incr(minute_key)
    pipe.expire(minute_key, 90)
    pipe.incr(day_key)
    pipe.expire(day_key, 90000)
    minute_count, _, day_count, _ = pipe.execute()
    return int(minute_count), int(day_count)


def _increment_fallback(minute_key: str, day_key: str) -> tuple[int, int]:
    now = int(_now_seconds())
    minute_count = _fallback_counts.get(minute_key, (0, now + 90))[0] + 1
    day_count = _fallback_counts.get(day_key, (0, now + 90000))[0] + 1
    _fallback_counts[minute_key] = (minute_count, now + 90)
    _fallback_counts[day_key] = (day_count, now + 90000)
    for key, (_, expires_at) in list(_fallback_counts.items()):
        if expires_at <= now:
            _fallback_counts.pop(key, None)
    return minute_count, day_count


def _now_seconds() -> float:
    return time.time()
