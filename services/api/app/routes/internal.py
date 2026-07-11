from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.dependencies import get_storage
from app.lifecycle import build_user_lifecycle_export, delete_user_lifecycle_data
from app.storage import S3Storage
from app.webhook_delivery import (
    WEBHOOK_RESPONSE_PREVIEW_CHARS,
    complete_webhook_delivery_attempt,
    prepare_webhook_delivery_attempt,
)

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


class WebhookAttemptResponse(BaseModel):
    url: str
    body: str
    headers: dict[str, str]
    timeout_seconds: float = Field(serialization_alias="timeoutSeconds")


class WebhookAttemptResultRequest(BaseModel):
    response_status_code: int | None = Field(default=None, alias="responseStatusCode")
    response_body_preview: str | None = Field(default=None, alias="responseBodyPreview")
    error: str | None = None


class WebhookAttemptResultResponse(BaseModel):
    status: str
    retry_delay_seconds: int | None = Field(default=None, serialization_alias="retryDelaySeconds")


class UserLifecycleRequest(BaseModel):
    action: str
    email: str
    requestId: str | None = None


@router.post("/webhook-deliveries/{delivery_id}/attempt", response_model=WebhookAttemptResponse)
def prepare_webhook_attempt(
    delivery_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
) -> WebhookAttemptResponse:
    _require_internal_token(settings, authorization)
    attempt = prepare_webhook_delivery_attempt(db, delivery_id)
    if attempt is None:
        raise HTTPException(status_code=409, detail="Webhook delivery is not deliverable.")
    return WebhookAttemptResponse.model_validate({**attempt, "timeout_seconds": 10.0})


@router.post("/webhook-deliveries/{delivery_id}/result", response_model=WebhookAttemptResultResponse)
def complete_webhook_attempt(
    delivery_id: str,
    payload: WebhookAttemptResultRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
) -> WebhookAttemptResultResponse:
    _require_internal_token(settings, authorization)
    delivery = complete_webhook_delivery_attempt(
        db,
        delivery_id,
        response_status_code=payload.response_status_code,
        response_body_preview=(payload.response_body_preview or "")[:WEBHOOK_RESPONSE_PREVIEW_CHARS],
        error=payload.error,
    )
    if delivery is None:
        raise HTTPException(status_code=404, detail="Webhook delivery not found.")
    retry_delay = None
    if delivery.status == "queued" and delivery.next_attempt_at:
        retry_at = delivery.next_attempt_at
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        retry_delay = max(int((retry_at - datetime.now(timezone.utc)).total_seconds()), 1)
    return WebhookAttemptResultResponse.model_validate({"status": delivery.status, "retry_delay_seconds": retry_delay})


@router.post("/lifecycle/{user_system_id}")
def user_lifecycle(
    user_system_id: str,
    payload: UserLifecycleRequest,
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
) -> dict:
    _require_lifecycle_token(settings, authorization)
    email = payload.email.strip().lower()
    if not user_system_id.strip() or "@" not in email:
        raise HTTPException(status_code=400, detail="User id and valid email are required.")
    if payload.action == "export":
        return {
            "ok": True,
            "service": "extract",
            "requestId": payload.requestId,
            "data": build_user_lifecycle_export(db, email),
        }
    if payload.action == "delete":
        return {
            "ok": True,
            "service": "extract",
            "requestId": payload.requestId,
            "deleted": delete_user_lifecycle_data(db, storage, email),
        }
    raise HTTPException(status_code=400, detail="Lifecycle action must be export or delete.")


@router.get("/sunset/census")
def sunset_census(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
) -> dict:
    _require_lifecycle_token(settings, authorization)

    def count(sql: str) -> int:
        return int(db.execute(text(sql)).scalar_one() or 0)

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "readOnlyMode": settings.read_only_mode,
        "sunsetAt": settings.sunset_at,
        "successor": settings.sunset_successor_url,
        "counts": {
            "users": count("SELECT COUNT(*) FROM users"),
            "activePaidSubscriptions": count(
                "SELECT COUNT(*) FROM subscriptions WHERE status IN ('active', 'trialing') AND plan != 'free'"
            ),
            "documents": count("SELECT COUNT(*) FROM documents"),
            "openBatchJobs": count(
                "SELECT COUNT(*) FROM batch_jobs WHERE status IN ('queued', 'running', 'retrying')"
            ),
            "pendingExports": count(
                "SELECT COUNT(*) FROM export_jobs WHERE status IN ('queued', 'running')"
            ),
        },
    }


def _require_internal_token(settings: Settings, authorization: str | None) -> None:
    if not settings.internal_worker_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="INTERNAL_WORKER_TOKEN is not configured.")
    expected = f"Bearer {settings.internal_worker_token}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal worker token.")


def _require_lifecycle_token(settings: Settings, authorization: str | None) -> None:
    if not settings.lifecycle_service_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LIFECYCLE_SERVICE_SECRET is not configured.")
    expected = f"Bearer {settings.lifecycle_service_secret}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid lifecycle service credential.")
