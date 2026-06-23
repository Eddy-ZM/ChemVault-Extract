from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, accessible_workspace_ids, require_workspace_permission
from app.database import get_db
from app.dependencies import get_webhook_delivery_queue
from app.models import User, WebhookDelivery, WebhookEndpoint
from app.queue import WebhookDeliveryQueue
from app.schemas import (
    WebhookDeliveryRead,
    WebhookEndpointCreateRequest,
    WebhookEndpointCreateResponse,
    WebhookEndpointRead,
    WebhookEndpointUpdateRequest,
    WebhookSecretRotateResponse,
)
from app.security import get_current_user
from app.webhook_delivery import (
    WEBHOOK_EVENTS,
    build_webhook_payload,
    configure_endpoint_secret,
    deliver_webhook_delivery,
    generate_webhook_secret,
)

router = APIRouter(prefix="/settings/webhooks", tags=["webhook-settings"])


@router.get("", response_model=list[WebhookEndpointRead])
def list_webhook_endpoints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WebhookEndpointRead]:
    workspace_ids = accessible_workspace_ids(db, current_user)
    filters = [and_(WebhookEndpoint.user_id == current_user.id, WebhookEndpoint.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(WebhookEndpoint.workspace_id.in_(workspace_ids))
    records = db.scalars(
        select(WebhookEndpoint)
        .where(or_(*filters))
        .order_by(WebhookEndpoint.created_at.desc(), WebhookEndpoint.id.desc())
    ).all()
    return [WebhookEndpointRead.model_validate(record) for record in records if _can_manage_endpoint(db, record, current_user)]


@router.post("", response_model=WebhookEndpointCreateResponse, status_code=status.HTTP_201_CREATED)
def create_webhook_endpoint(
    payload: WebhookEndpointCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WebhookEndpointCreateResponse:
    url = _validate_webhook_url(payload.url)
    events = _validate_events(payload.events)

    workspace_id = payload.resolved_workspace_id
    if workspace_id:
        require_workspace_permission(db, workspace_id, current_user, Permission.MANAGE_WORKSPACE)

    secret = generate_webhook_secret()
    record = WebhookEndpoint(
        user_id=current_user.id,
        workspace_id=workspace_id,
        url=url,
        secret_hash="",
        events=events,
        is_active=True,
    )
    configure_endpoint_secret(record, secret)
    db.add(record)
    db.commit()
    db.refresh(record)
    return _endpoint_create_response(record, secret)


@router.get("/{webhook_endpoint_id}", response_model=WebhookEndpointRead)
def get_webhook_endpoint(
    webhook_endpoint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WebhookEndpointRead:
    record = _endpoint_or_404(db, webhook_endpoint_id)
    _require_manage_endpoint(db, record, current_user)
    return WebhookEndpointRead.model_validate(record)


@router.patch("/{webhook_endpoint_id}", response_model=WebhookEndpointRead)
def update_webhook_endpoint(
    webhook_endpoint_id: str,
    payload: WebhookEndpointUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WebhookEndpointRead:
    record = _endpoint_or_404(db, webhook_endpoint_id)
    _require_manage_endpoint(db, record, current_user)
    if payload.url is not None:
        record.url = _validate_webhook_url(payload.url)
    if payload.events is not None:
        record.events = _validate_events(payload.events)
    if payload.isActive is not None:
        record.is_active = payload.isActive
    db.commit()
    db.refresh(record)
    return WebhookEndpointRead.model_validate(record)


@router.delete("/{webhook_endpoint_id}", response_model=WebhookEndpointRead)
def delete_webhook_endpoint(
    webhook_endpoint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WebhookEndpointRead:
    record = _endpoint_or_404(db, webhook_endpoint_id)
    _require_manage_endpoint(db, record, current_user)
    record.is_active = False
    db.commit()
    db.refresh(record)
    return WebhookEndpointRead.model_validate(record)


@router.post("/{webhook_endpoint_id}/rotate-secret", response_model=WebhookSecretRotateResponse)
def rotate_webhook_secret(
    webhook_endpoint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WebhookSecretRotateResponse:
    record = _endpoint_or_404(db, webhook_endpoint_id)
    _require_manage_endpoint(db, record, current_user)
    secret = generate_webhook_secret()
    configure_endpoint_secret(record, secret)
    db.commit()
    db.refresh(record)
    return WebhookSecretRotateResponse.model_validate(
        {"id": record.id, "secret_preview": record.secret_preview, "signing_secret": secret}
    )


@router.post("/{webhook_endpoint_id}/test", response_model=WebhookDeliveryRead, status_code=status.HTTP_201_CREATED)
def send_test_webhook(
    webhook_endpoint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    queue: WebhookDeliveryQueue = Depends(get_webhook_delivery_queue),
) -> WebhookDeliveryRead:
    record = _endpoint_or_404(db, webhook_endpoint_id)
    _require_manage_endpoint(db, record, current_user)
    payload = build_webhook_payload(
        event_type="webhook.test",
        workspace_id=record.workspace_id,
        data={"message": "ChemVault webhook test event."},
    )
    delivery = WebhookDelivery(
        webhook_endpoint_id=record.id,
        event_id=payload["id"],
        event_type="webhook.test",
        payload=payload,
        status="queued",
        next_attempt_at=datetime.now(timezone.utc),
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    try:
        delivered = deliver_webhook_delivery(db, delivery.id)
    except Exception:
        queue.push_delivery(delivery.id)
        db.refresh(delivery)
        delivered = delivery
    return WebhookDeliveryRead.model_validate(delivered or delivery)


@router.get("/{webhook_endpoint_id}/deliveries", response_model=list[WebhookDeliveryRead])
def list_webhook_deliveries(
    webhook_endpoint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WebhookDeliveryRead]:
    record = _endpoint_or_404(db, webhook_endpoint_id)
    _require_manage_endpoint(db, record, current_user)
    deliveries = db.scalars(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_endpoint_id == record.id)
        .order_by(WebhookDelivery.created_at.desc(), WebhookDelivery.id.desc())
        .limit(100)
    ).all()
    return [WebhookDeliveryRead.model_validate(delivery) for delivery in deliveries]


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryRead)
def get_webhook_delivery(
    delivery_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WebhookDeliveryRead:
    delivery = db.get(WebhookDelivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Webhook delivery not found.")
    _require_manage_endpoint(db, delivery.webhook_endpoint, current_user)
    return WebhookDeliveryRead.model_validate(delivery)


def _endpoint_or_404(db: Session, webhook_endpoint_id: str) -> WebhookEndpoint:
    record = db.get(WebhookEndpoint, webhook_endpoint_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found.")
    return record


def _can_manage_endpoint(db: Session, endpoint: WebhookEndpoint, user: User) -> bool:
    try:
        _require_manage_endpoint(db, endpoint, user)
        return True
    except HTTPException:
        return False


def _require_manage_endpoint(db: Session, endpoint: WebhookEndpoint | None, user: User) -> None:
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found.")
    if endpoint.workspace_id:
        require_workspace_permission(db, endpoint.workspace_id, user, Permission.MANAGE_WORKSPACE)
        return
    if endpoint.user_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this webhook endpoint.")


def _validate_webhook_url(value: str) -> str:
    url = value.strip()
    if not (url.startswith("https://") or url.startswith("http://localhost") or url.startswith("http://127.0.0.1")):
        raise HTTPException(status_code=400, detail="Webhook URL must use HTTPS or localhost for development.")
    return url


def _validate_events(values: list[str]) -> list[str]:
    events = sorted(set(values))
    invalid_events = [event for event in events if event not in WEBHOOK_EVENTS or event == "webhook.test"]
    if invalid_events:
        raise HTTPException(status_code=400, detail=f"Invalid webhook events: {', '.join(invalid_events)}")
    if not events:
        raise HTTPException(status_code=400, detail="At least one webhook event is required.")
    return events


def _endpoint_create_response(record: WebhookEndpoint, secret: str) -> WebhookEndpointCreateResponse:
    return WebhookEndpointCreateResponse.model_validate(
        {
            "id": record.id,
            "workspace_id": record.workspace_id,
            "url": record.url,
            "secret_preview": record.secret_preview,
            "events": record.events,
            "is_active": record.is_active,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "signing_secret": secret,
        }
    )
