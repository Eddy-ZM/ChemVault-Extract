from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
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


def _require_internal_token(settings: Settings, authorization: str | None) -> None:
    if not settings.internal_worker_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="INTERNAL_WORKER_TOKEN is not configured.")
    expected = f"Bearer {settings.internal_worker_token}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal worker token.")
