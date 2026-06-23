from __future__ import annotations

import hmac
import io
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.api_keys import hash_api_key
from app.database import SessionLocal
from app.models import User, WebhookDelivery, WebhookEndpoint
from app.security import decrypt_secret
from app.webhook_delivery import (
    build_webhook_payload,
    configure_endpoint_secret,
    deliver_webhook_delivery,
)


def test_create_webhook_endpoint_returns_secret_once_and_stores_no_plaintext(api_client):
    response = api_client.post(
        "/settings/webhooks",
        json={"url": "https://example.com/webhook", "events": ["document.uploaded", "extraction.completed"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["signingSecret"].startswith("whsec_")
    assert body["secretPreview"].startswith("whsec_****")

    list_response = api_client.get("/settings/webhooks")
    assert list_response.status_code == 200
    assert "signingSecret" not in list_response.json()[0]

    with SessionLocal() as db:
        endpoint = db.get(WebhookEndpoint, body["id"])
        assert endpoint is not None
        assert endpoint.secret_hash == hash_api_key(body["signingSecret"])
        assert endpoint.encrypted_secret != body["signingSecret"]
        assert endpoint.secret_preview == body["secretPreview"]


def test_rotate_webhook_secret_replaces_active_secret(api_client):
    created = api_client.post(
        "/settings/webhooks",
        json={"url": "https://example.com/webhook", "events": ["document.uploaded"]},
    ).json()
    old_secret = created["signingSecret"]
    old_hash = hash_api_key(old_secret)

    response = api_client.post(f"/settings/webhooks/{created['id']}/rotate-secret")

    assert response.status_code == 200
    body = response.json()
    assert body["signingSecret"].startswith("whsec_")
    assert body["signingSecret"] != old_secret
    with SessionLocal() as db:
        endpoint = db.get(WebhookEndpoint, created["id"])
        assert endpoint is not None
        assert endpoint.secret_hash != old_hash
        assert endpoint.secret_hash == hash_api_key(body["signingSecret"])


def test_deliver_webhook_adds_hmac_signature_header(api_client):
    secret = "whsec_unit_test_secret"
    with SessionLocal() as db:
        endpoint = _create_endpoint(db, secret=secret)
        delivery = _create_delivery(db, endpoint)
        captured: dict[str, str | bytes] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = request.content
            captured["timestamp"] = request.headers["X-ChemVault-Timestamp"]
            captured["signature"] = request.headers["X-ChemVault-Signature"]
            captured["event"] = request.headers["X-ChemVault-Event"]
            captured["delivery"] = request.headers["X-ChemVault-Delivery"]
            return httpx.Response(204)

        result = deliver_webhook_delivery(
            db,
            delivery.id,
            client=httpx.Client(transport=httpx.MockTransport(handler)),
        )

        assert result is not None
        assert result.status == "delivered"
        assert captured["event"] == "extraction.completed"
        assert captured["delivery"] == delivery.id
        expected_signature = _expected_signature(secret, captured["timestamp"], captured["body"])
        assert hmac.compare_digest(captured["signature"], expected_signature)


def test_failed_webhook_delivery_retries_then_fails(api_client):
    with SessionLocal() as db:
        endpoint = _create_endpoint(db)
        delivery = _create_delivery(db, endpoint)

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="receiver failed")

        result = deliver_webhook_delivery(
            db,
            delivery.id,
            client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        assert result is not None
        assert result.status == "queued"
        assert result.attempt_count == 1
        assert result.response_status_code == 500
        assert result.response_body_preview == "receiver failed"
        assert result.next_attempt_at is not None

        result.attempt_count = result.max_attempts - 1
        result.next_attempt_at = datetime.now(timezone.utc)
        db.commit()
        failed = deliver_webhook_delivery(
            db,
            result.id,
            client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        assert failed is not None
        assert failed.status == "failed"
        assert failed.attempt_count == failed.max_attempts


def test_inactive_webhook_endpoint_cancels_delivery(api_client):
    with SessionLocal() as db:
        endpoint = _create_endpoint(db)
        endpoint.is_active = False
        delivery = _create_delivery(db, endpoint)
        db.commit()

        result = deliver_webhook_delivery(db, delivery.id, client=httpx.Client(transport=httpx.MockTransport(_boom)))

        assert result is not None
        assert result.status == "cancelled"
        assert "inactive" in (result.error or "")


def test_document_uploaded_event_creates_and_queues_delivery(api_client, fake_webhook_queue):
    endpoint = api_client.post(
        "/settings/webhooks",
        json={"url": "https://example.com/webhook", "events": ["document.uploaded"]},
    ).json()

    upload = api_client.post(
        "/documents/upload",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert upload.status_code == 201
    with SessionLocal() as db:
        deliveries = db.scalars(
            select(WebhookDelivery).where(WebhookDelivery.webhook_endpoint_id == endpoint["id"])
        ).all()
        assert len(deliveries) == 1
        assert deliveries[0].event_type == "document.uploaded"
        assert deliveries[0].payload["document_id"] == upload.json()["document"]["id"]
        assert fake_webhook_queue.pushed == [deliveries[0].id]


def _create_endpoint(db, *, secret: str = "whsec_unit_test_secret") -> WebhookEndpoint:
    user = db.scalars(select(User).where(User.email == "test@example.com")).one()
    endpoint = WebhookEndpoint(
        user_id=user.id,
        url="https://example.com/webhook",
        secret_hash="",
        events=["extraction.completed"],
        is_active=True,
    )
    configure_endpoint_secret(endpoint, secret)
    assert decrypt_secret(endpoint.encrypted_secret) == secret
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


def _create_delivery(db, endpoint: WebhookEndpoint) -> WebhookDelivery:
    payload = build_webhook_payload(
        event_type="extraction.completed",
        project_id="proj_123",
        document_id="doc_123",
        data={"job_id": "job_123", "records_url": "/v1/documents/doc_123/records"},
    )
    delivery = WebhookDelivery(
        webhook_endpoint_id=endpoint.id,
        event_id=payload["id"],
        event_type=payload["type"],
        payload=payload,
        status="queued",
        next_attempt_at=datetime.now(timezone.utc),
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


def _expected_signature(secret: str, timestamp: str, body: bytes) -> str:
    import hashlib

    digest = hmac.new(secret.encode("utf-8"), timestamp.encode("utf-8") + b"." + body, hashlib.sha256).hexdigest()
    return f"v1={digest}"


def _boom(_: httpx.Request) -> httpx.Response:
    raise AssertionError("inactive endpoint should not send HTTP request")
