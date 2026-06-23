from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api_keys import hash_api_key
from app.models import Document, Project, WebhookDelivery, WebhookEndpoint
from app.queue import WebhookDeliveryQueue
from app.security import decrypt_secret, encrypt_secret

WEBHOOK_API_VERSION = "2026-06-01"
WEBHOOK_MAX_ATTEMPTS = 5
WEBHOOK_RESPONSE_PREVIEW_CHARS = 2000
WEBHOOK_TIMEOUT_SECONDS = 10.0
RETRY_DELAYS_SECONDS = [0, 60, 300, 1800, 7200]

WEBHOOK_EVENTS = {
    "document.uploaded",
    "document.parsed",
    "document.parse_failed",
    "extraction.started",
    "extraction.completed",
    "extraction.failed",
    "normalization.completed",
    "normalization.failed",
    "review.item_created",
    "review.item_approved",
    "review.item_rejected",
    "export.completed",
    "export.failed",
    "batch.completed",
    "batch.partial_failed",
    "batch.failed",
    "webhook.test",
}


def generate_webhook_secret() -> str:
    return f"whsec_{secrets.token_urlsafe(32)}"


def preview_webhook_secret(secret: str) -> str:
    return f"whsec_****{secret[-4:]}"


def build_webhook_payload(
    *,
    event_type: str,
    workspace_id: str | None = None,
    project_id: str | None = None,
    document_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"evt_{uuid.uuid4().hex}",
        "type": event_type,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workspace_id": workspace_id,
        "project_id": project_id,
        "document_id": document_id,
        "data": data or {},
        "api_version": WEBHOOK_API_VERSION,
    }


def configure_endpoint_secret(endpoint: WebhookEndpoint, secret: str) -> None:
    endpoint.secret_hash = hash_api_key(secret)
    endpoint.encrypted_secret = encrypt_secret(secret)
    endpoint.secret_preview = preview_webhook_secret(secret)


def enqueue_webhook_event_for_document(
    db: Session,
    queue: WebhookDeliveryQueue | None,
    *,
    document: Document,
    event_type: str,
    data: dict[str, Any] | None = None,
) -> list[WebhookDelivery]:
    project = document.project or db.get(Project, document.project_id)
    if project is None:
        return []
    return enqueue_webhook_event(
        db,
        queue,
        user_id=project.user_id,
        workspace_id=project.workspace_id,
        project_id=project.id,
        document_id=document.id,
        event_type=event_type,
        data=data,
    )


def enqueue_webhook_event(
    db: Session,
    queue: WebhookDeliveryQueue | None,
    *,
    event_type: str,
    user_id: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
    document_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> list[WebhookDelivery]:
    if event_type not in WEBHOOK_EVENTS:
        return []
    payload = build_webhook_payload(
        event_type=event_type,
        workspace_id=workspace_id,
        project_id=project_id,
        document_id=document_id,
        data=data,
    )
    endpoints = _matching_endpoints(db, event_type, user_id=user_id, workspace_id=workspace_id)
    deliveries: list[WebhookDelivery] = []
    now = datetime.now(timezone.utc)
    for endpoint in endpoints:
        delivery = WebhookDelivery(
            webhook_endpoint_id=endpoint.id,
            event_id=payload["id"],
            event_type=event_type,
            payload=payload,
            status="queued",
            attempt_count=0,
            max_attempts=WEBHOOK_MAX_ATTEMPTS,
            next_attempt_at=now,
        )
        db.add(delivery)
        db.flush()
        deliveries.append(delivery)
        if queue is not None:
            queue.push_delivery(delivery.id)
    return deliveries


def enqueue_due_webhook_deliveries(db: Session, queue: WebhookDeliveryQueue, *, limit: int = 50) -> int:
    now = datetime.now(timezone.utc)
    deliveries = db.scalars(
        select(WebhookDelivery)
        .where(
            WebhookDelivery.status == "queued",
            or_(WebhookDelivery.next_attempt_at.is_(None), WebhookDelivery.next_attempt_at <= now),
        )
        .order_by(WebhookDelivery.next_attempt_at, WebhookDelivery.created_at)
        .limit(limit)
    ).all()
    for delivery in deliveries:
        queue.push_delivery(delivery.id)
    return len(deliveries)


def deliver_webhook_delivery(
    db: Session,
    delivery_id: str,
    *,
    client: httpx.Client | None = None,
) -> WebhookDelivery | None:
    attempt = prepare_webhook_delivery_attempt(db, delivery_id)
    if attempt is None:
        return db.get(WebhookDelivery, delivery_id)

    close_client = client is None
    http_client = client or httpx.Client(timeout=WEBHOOK_TIMEOUT_SECONDS)
    try:
        response = http_client.post(attempt["url"], content=attempt["body"], headers=attempt["headers"])
        return complete_webhook_delivery_attempt(
            db,
            delivery_id,
            response_status_code=response.status_code,
            response_body_preview=response.text[:WEBHOOK_RESPONSE_PREVIEW_CHARS],
            error=None,
        )
    except Exception as exc:  # noqa: BLE001
        return complete_webhook_delivery_attempt(db, delivery_id, response_status_code=None, error=str(exc))
    finally:
        if close_client:
            http_client.close()


def prepare_webhook_delivery_attempt(db: Session, delivery_id: str) -> dict[str, Any] | None:
    delivery = db.get(WebhookDelivery, delivery_id)
    if delivery is None:
        return None
    if delivery.status in {"delivered", "failed", "cancelled"}:
        return delivery
    now = datetime.now(timezone.utc)
    if delivery.next_attempt_at and _as_aware(delivery.next_attempt_at) > now:
        return delivery
    endpoint = delivery.webhook_endpoint
    if endpoint is None or not endpoint.is_active:
        delivery.status = "cancelled"
        delivery.error = "Webhook endpoint is inactive."
        db.commit()
        db.refresh(delivery)
        return None
    if not endpoint.encrypted_secret:
        _mark_delivery_failed(delivery, "Webhook endpoint signing secret is not available.")
        db.commit()
        db.refresh(delivery)
        return None

    delivery.status = "delivering"
    delivery.attempt_count += 1
    delivery.error = None
    db.commit()
    db.refresh(delivery)

    raw_body = json.dumps(delivery.payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    secret = decrypt_secret(endpoint.encrypted_secret)
    signature = sign_webhook_payload(secret, timestamp, raw_body)
    headers = {
        "content-type": "application/json",
        "user-agent": "ChemVault-Webhook/1.0",
        "X-ChemVault-Event": delivery.event_type,
        "X-ChemVault-Delivery": delivery.id,
        "X-ChemVault-Timestamp": timestamp,
        "X-ChemVault-Signature": signature,
    }
    return {"url": endpoint.url, "body": raw_body.decode("utf-8"), "headers": headers}


def complete_webhook_delivery_attempt(
    db: Session,
    delivery_id: str,
    *,
    response_status_code: int | None,
    response_body_preview: str | None = None,
    error: str | None = None,
) -> WebhookDelivery | None:
    delivery = db.get(WebhookDelivery, delivery_id)
    if delivery is None:
        return None
    if delivery.status in {"delivered", "failed", "cancelled"}:
        return delivery

    delivery.response_status_code = response_status_code
    delivery.response_body_preview = (response_body_preview or "")[:WEBHOOK_RESPONSE_PREVIEW_CHARS] or None
    if response_status_code is not None and 200 <= response_status_code < 300:
        delivery.status = "delivered"
        delivery.error = None
        delivery.delivered_at = datetime.now(timezone.utc)
        delivery.next_attempt_at = None
    else:
        _schedule_retry(delivery, error or f"Webhook returned HTTP {response_status_code}.")

    db.commit()
    db.refresh(delivery)
    return delivery


def sign_webhook_payload(secret: str, timestamp: str, raw_body: bytes) -> str:
    signed_payload = timestamp.encode("utf-8") + b"." + raw_body
    digest = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"v1={digest}"


def _matching_endpoints(
    db: Session,
    event_type: str,
    *,
    user_id: str | None,
    workspace_id: str | None,
) -> list[WebhookEndpoint]:
    if workspace_id:
        endpoints = db.scalars(
            select(WebhookEndpoint).where(WebhookEndpoint.workspace_id == workspace_id, WebhookEndpoint.is_active.is_(True))
        ).all()
    elif user_id:
        endpoints = db.scalars(
            select(WebhookEndpoint).where(
                WebhookEndpoint.user_id == user_id,
                WebhookEndpoint.workspace_id.is_(None),
                WebhookEndpoint.is_active.is_(True),
            )
        ).all()
    else:
        endpoints = []
    return [endpoint for endpoint in endpoints if event_type in (endpoint.events or []) or event_type == "webhook.test"]


def _schedule_retry(delivery: WebhookDelivery, error: str) -> None:
    delivery.error = error
    if delivery.attempt_count >= delivery.max_attempts:
        delivery.status = "failed"
        delivery.next_attempt_at = None
        return
    delivery.status = "queued"
    delay_index = min(delivery.attempt_count, len(RETRY_DELAYS_SECONDS) - 1)
    delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=RETRY_DELAYS_SECONDS[delay_index])


def _mark_delivery_failed(delivery: WebhookDelivery, error: str) -> None:
    delivery.status = "failed"
    delivery.error = error
    delivery.next_attempt_at = None


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
