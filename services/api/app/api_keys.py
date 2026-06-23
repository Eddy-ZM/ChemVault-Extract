from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from app.models import ApiKey

API_KEY_SCOPES = {
    "documents:read",
    "documents:write",
    "extractions:read",
    "extractions:write",
    "records:read",
    "exports:read",
    "exports:write",
    "projects:read",
    "projects:write",
}


def generate_api_key(*, test_mode: bool = False) -> str:
    prefix = "cv_test" if test_mode else "cv_live"
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_api_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key_prefix(value: str) -> str:
    return value[:16]


def mask_api_key(value: str) -> str:
    suffix = value[-4:] if len(value) >= 4 else "****"
    if value.startswith("cv_test_"):
        return f"cv_test_****{suffix}"
    return f"cv_live_****{suffix}"


def validate_api_key_format(value: str) -> bool:
    return value.startswith("cv_live_") or value.startswith("cv_test_")


def is_api_key_active(record: ApiKey, now: datetime | None = None) -> tuple[bool, str | None]:
    resolved_now = now or datetime.now(timezone.utc)
    if record.revoked_at is not None:
        return False, "api_key_revoked"
    if record.expires_at is not None and _as_aware(record.expires_at) <= resolved_now:
        return False, "api_key_expired"
    return True, None


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
