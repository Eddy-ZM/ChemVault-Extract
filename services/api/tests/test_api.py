import io
import json
import time
import hmac
import hashlib

from sqlalchemy import inspect
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings
from app.models import (
    AiUsageRecord,
    ApiKey,
    ApiRequestLog,
    BatchJob,
    BatchJobItem,
    BillingEvent,
    ContactMessage,
    Subscription,
    User,
)


def test_health_returns_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["storage"] == "ok"
    assert body["queue"] == "ok"


def test_protected_upload_requires_login():
    client = TestClient(app)

    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", io.BytesIO(b"private"), "text/plain")},
    )

    assert response.status_code == 401


def test_registered_password_is_hashed(api_client):
    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.email == "test@example.com")).first()

    assert user is not None
    assert user.password_hash != "test-password-123"
    assert user.password_hash


def test_register_requires_turnstile_when_enabled(monkeypatch):
    monkeypatch.setenv("TURNSTILE_REQUIRED", "true")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "turnstile-test-secret")
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={"email": "turnstile-missing@example.com", "password": "test-password-123"},
    )

    assert response.status_code == 400
    assert "Turnstile verification is required" in response.json()["detail"]
    get_settings.cache_clear()


def test_register_verifies_turnstile_token(monkeypatch):
    captured: dict[str, object] = {}

    class FakeTurnstileResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, bool]:
            return {"success": True}

    def fake_post(url, data, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        return FakeTurnstileResponse()

    monkeypatch.setenv("TURNSTILE_REQUIRED", "true")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "turnstile-test-secret")
    monkeypatch.setattr("app.turnstile.httpx.post", fake_post)
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={
            "email": "turnstile-valid@example.com",
            "password": "test-password-123",
            "turnstileToken": "cf-response-token",
        },
    )

    assert response.status_code == 201
    assert captured["data"]["secret"] == "turnstile-test-secret"
    assert captured["data"]["response"] == "cf-response-token"
    get_settings.cache_clear()


def test_upload_rejects_unsupported_file_type(api_client):
    response = api_client.post(
        "/documents/upload",
        files={"file": ("sample.exe", io.BytesIO(b"not allowed"), "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_stores_file_creates_document_and_queues_job(api_client, fake_storage, fake_queue):
    response = api_client.post(
        "/documents/upload",
        files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document"]["originalFilename"] == "report.pdf"
    assert body["document"]["fileType"] == "pdf"
    assert body["document"]["status"] == "uploaded"
    assert body["job"]["status"] == "queued"
    assert fake_storage.saved[0]["key"] == body["document"]["storageKey"]
    assert fake_queue.pushed == [body["job"]["id"]]


def test_document_detail_includes_latest_job(api_client):
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("notes.md", io.BytesIO(b"# Notes"), "text/markdown")},
    ).json()

    response = api_client.get(f"/documents/{upload['document']['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == upload["document"]["id"]
    assert body["latestJob"]["id"] == upload["job"]["id"]
    assert body["latestJob"]["status"] == "queued"


def test_extract_endpoint_creates_new_queued_job(api_client, fake_queue):
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("table.csv", io.BytesIO(b"a,b\n1,2"), "text/csv")},
    ).json()

    response = api_client.post(f"/documents/{upload['document']['id']}/extract")

    assert response.status_code == 201
    body = response.json()
    assert body["documentId"] == upload["document"]["id"]
    assert body["status"] == "queued"
    assert fake_queue.pushed[-1] == body["id"]


def test_free_plan_project_limit_is_enforced(api_client):
    first = api_client.post("/projects", json={"name": "Second project"})
    second = api_client.post("/projects", json={"name": "Third project"})

    assert first.status_code == 201
    assert second.status_code == 400
    assert "Project limit reached" in second.json()["detail"]


def test_free_plan_batch_extraction_is_blocked(api_client):
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("batch.txt", io.BytesIO(b"batch"), "text/plain")},
    ).json()

    response = api_client.post("/documents/batch-extract-ai", json={"documentIds": [upload["document"]["id"]]})

    assert response.status_code == 403
    assert "Batch extraction" in response.json()["detail"]


def test_free_plan_cannot_create_workspace(api_client):
    response = api_client.post("/workspaces", json={"name": "Shared lab"})

    assert response.status_code == 403
    assert "team workspaces" in response.json()["detail"]


def test_workspace_invite_accept_and_member_batch_upload(api_client, fake_queue):
    _set_user_plan("test@example.com", "lab")
    workspace_response = api_client.post("/workspaces", json={"name": "Shared lab"})
    assert workspace_response.status_code == 201
    workspace = workspace_response.json()

    project_response = api_client.post(
        "/projects",
        json={"name": "Team project", "workspace_id": workspace["id"]},
    )
    assert project_response.status_code == 201
    project = project_response.json()
    assert project["workspaceId"] == workspace["id"]

    invite_response = api_client.post(
        f"/workspaces/{workspace['id']}/invites",
        json={"email": "member@example.com", "role": "member"},
    )
    assert invite_response.status_code == 201
    invite = invite_response.json()

    register_response = api_client.post(
        "/auth/register",
        json={"email": "member@example.com", "password": "member-password-123", "name": "Member"},
    )
    assert register_response.status_code == 201
    member_token = register_response.json()["accessToken"]
    api_client.headers.update({"authorization": f"Bearer {member_token}"})

    accept_response = api_client.post(f"/workspaces/invites/{invite['inviteToken']}/accept")
    assert accept_response.status_code == 200
    assert accept_response.json()["member"]["status"] == "active"

    forbidden_project = api_client.post(
        "/projects",
        json={"name": "Member-created project", "workspace_id": workspace["id"]},
    )
    assert forbidden_project.status_code == 403

    upload_response = api_client.post(
        "/documents/batch-upload",
        data={"project_id": project["id"]},
        files=[
            ("files", ("one.txt", io.BytesIO(b"first"), "text/plain")),
            ("files", ("two.md", io.BytesIO(b"# second"), "text/markdown")),
        ],
    )
    assert upload_response.status_code == 201
    body = upload_response.json()
    assert body["documents"] == 2
    assert len(body["jobs"]) == 2
    assert fake_queue.pushed[-2:] == [job["id"] for job in body["jobs"]]

    with SessionLocal() as db:
        batch = db.get(BatchJob, body["batchJobId"])
        assert batch is not None
        assert batch.workspace_id == workspace["id"]
        assert batch.total_items == 2
        assert len(batch.items) == 2


def test_researcher_can_create_batch_ai_job(api_client, monkeypatch, fake_queue):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()
    _set_user_plan("test@example.com", "researcher")
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("extract.txt", io.BytesIO(b"Organic synthesis procedure"), "text/plain")},
    ).json()

    response = api_client.post(
        "/batch/extract-ai",
        json={
            "project_id": upload["document"]["projectId"],
            "document_ids": [upload["document"]["id"]],
            "mode": "selected",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["documents"] == 1
    assert body["batchJob"]["type"] == "ai_extraction"
    assert fake_queue.pushed[-1] != upload["job"]["id"]

    with SessionLocal() as db:
        batch = db.get(BatchJob, body["batchJobId"])
        assert batch is not None
        assert batch.total_items == 1
        item = db.scalars(select(BatchJobItem).where(BatchJobItem.batch_job_id == batch.id)).first()
        assert item is not None
        usage = db.scalars(select(AiUsageRecord).where(AiUsageRecord.batch_job_id == batch.id)).first()
        assert usage is not None
        assert usage.document_id == upload["document"]["id"]


def test_public_contact_message_is_saved(api_client):
    api_client.headers.pop("authorization", None)

    response = api_client.post(
        "/contact",
        json={
            "name": "Ada Chemist",
            "email": "Ada@Example.com",
            "role": "PI",
            "organization": "Example Lab",
            "message": "We want to digitize lab reports.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["organization"] == "Example Lab"

    with SessionLocal() as db:
        message = db.get(ContactMessage, body["id"])
        assert message is not None
        assert message.message == "We want to digitize lab reports."


def test_api_key_creation_hashes_key_and_allows_v1_projects(api_client):
    create_response = api_client.post(
        "/settings/api-keys",
        json={"name": "Integration key", "scopes": ["projects:read"]},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    raw_key = created["plainKey"]
    assert raw_key.startswith("cv_live_")
    assert created["maskedKey"].startswith("cv_live_****")

    list_response = api_client.get("/settings/api-keys")
    assert list_response.status_code == 200
    assert "plainKey" not in list_response.json()[0]

    with SessionLocal() as db:
        record = db.get(ApiKey, created["id"])
        assert record is not None
        assert record.key_hash != raw_key
        assert raw_key not in record.key_hash

    response = api_client.get("/v1/projects", headers={"authorization": f"Bearer {raw_key}"})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Default Project"
    with SessionLocal() as db:
        refreshed = db.get(ApiKey, created["id"])
        assert refreshed is not None
        assert refreshed.last_used_at is not None
        log = db.scalars(select(ApiRequestLog).where(ApiRequestLog.api_key_id == created["id"])).first()
        assert log is not None
        assert log.path == "/v1/projects"


def test_v1_scope_is_enforced(api_client):
    create_response = api_client.post(
        "/settings/api-keys",
        json={"name": "Documents only", "scopes": ["documents:read"]},
    )
    raw_key = create_response.json()["plainKey"]

    response = api_client.get("/v1/projects", headers={"authorization": f"Bearer {raw_key}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "insufficient_scope"


def test_revoked_api_key_cannot_call_v1(api_client):
    create_response = api_client.post(
        "/settings/api-keys",
        json={"name": "Temporary", "scopes": ["projects:read"]},
    )
    body = create_response.json()
    revoke_response = api_client.post(f"/settings/api-keys/{body['id']}/revoke")
    assert revoke_response.status_code == 200

    response = api_client.get("/v1/projects", headers={"authorization": f"Bearer {body['plainKey']}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "api_key_revoked"


def test_v1_document_upload_uses_api_key_scope(api_client, fake_storage, fake_queue):
    project = api_client.get("/projects").json()[0]
    create_response = api_client.post(
        "/settings/api-keys",
        json={"name": "Upload key", "scopes": ["documents:write", "documents:read"]},
    )
    raw_key = create_response.json()["plainKey"]

    response = api_client.post(
        "/v1/documents",
        headers={"authorization": f"Bearer {raw_key}"},
        data={"project_id": project["id"], "auto_parse": "true"},
        files={"file": ("api-upload.txt", io.BytesIO(b"api upload"), "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "api-upload.txt"
    assert body["parse_job_id"] == fake_queue.pushed[-1]
    assert fake_storage.saved[-1]["key"].endswith("/api-upload.txt")


def test_v1_rate_limit_is_enforced(api_client):
    create_response = api_client.post(
        "/settings/api-keys",
        json={"name": "Rate key", "scopes": ["projects:read"]},
    )
    raw_key = create_response.json()["plainKey"]
    headers = {"authorization": f"Bearer {raw_key}"}

    final_response = None
    for _ in range(61):
        final_response = api_client.get("/v1/projects", headers=headers)

    assert final_response is not None
    assert final_response.status_code == 429
    assert final_response.json()["error"]["code"] == "rate_limit_exceeded"


def test_stripe_subscription_webhook_updates_plan(api_client):
    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.email == "test@example.com")).first()
        assert user is not None
        user_id = user.id
        customer_id = "cus_test"
        subscription_id = "sub_test"
        subscription = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).first()
        assert subscription is not None
        subscription.stripe_customer_id = customer_id
        subscription.stripe_subscription_id = subscription_id
        db.commit()

    event = {
        "id": "evt_test_subscription_updated",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": subscription_id,
                "object": "subscription",
                "customer": customer_id,
                "status": "active",
                "current_period_start": 1760000000,
                "current_period_end": 1762592000,
                "cancel_at_period_end": False,
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": "price_researcher_monthly",
                                "recurring": {"interval": "month"},
                            }
                        }
                    ]
                },
                "metadata": {"userId": user_id},
            }
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(b"whsec_test_secret", timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()

    response = api_client.post(
        "/webhooks/stripe",
        content=body,
        headers={"stripe-signature": f"t={timestamp},v1={signature}", "content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.email == "test@example.com")).first()
        assert user is not None
        assert user.plan == "researcher"
        assert user.monthly_ai_file_limit == 500
        event_record = db.scalars(select(BillingEvent).where(BillingEvent.stripe_event_id == event["id"])).first()
        assert event_record is not None


def test_scientific_record_tables_are_registered(api_client):
    inspector = inspect(engine)

    assert {
        "projects",
        "users",
        "user_ai_settings",
        "ai_usage_records",
        "subscriptions",
        "billing_events",
        "audit_logs",
        "workspaces",
        "workspace_members",
        "batch_jobs",
        "batch_job_items",
        "contact_messages",
        "api_keys",
        "api_request_logs",
        "webhook_endpoints",
        "webhook_deliveries",
        "documents",
        "document_pages",
        "document_blocks",
        "document_chunks",
        "extraction_jobs",
        "extraction_runs",
        "chemical_entities",
        "reaction_records",
        "measurement_records",
        "review_items",
        "export_jobs",
    }.issubset(set(inspector.get_table_names()))

    for table_name in ("chemical_entities", "reaction_records", "measurement_records"):
        column_names = {column["name"] for column in inspector.get_columns(table_name)}
        assert "evidence" in column_names


def _set_user_plan(email: str, plan: str) -> None:
    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.email == email)).first()
        assert user is not None
        user.plan_override = plan
        db.commit()
