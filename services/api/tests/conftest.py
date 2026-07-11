import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["S3_ENDPOINT"] = "http://localhost:9000"
os.environ["S3_ACCESS_KEY"] = "test"
os.environ["S3_SECRET_KEY"] = "test"
os.environ["S3_BUCKET"] = "test-bucket"
os.environ["STORAGE_PROVIDER"] = "minio"
os.environ["QUEUE_PROVIDER"] = "redis"
os.environ["AI_PROVIDER"] = "openai"
os.environ["JWT_SECRET"] = "test-jwt-secret"
os.environ["APP_ENCRYPTION_KEY"] = "test-encryption-key"
os.environ["INTERNAL_WORKER_TOKEN"] = "test-internal-token"
os.environ["LIFECYCLE_SERVICE_SECRET"] = "test-lifecycle-secret"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_placeholder"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_secret"
os.environ["STRIPE_PRICE_STUDENT_MONTHLY"] = "price_student_monthly"
os.environ["STRIPE_PRICE_RESEARCHER_MONTHLY"] = "price_researcher_monthly"
os.environ["STRIPE_PRICE_LAB_MONTHLY"] = "price_lab_monthly"
os.environ["STRIPE_PRICE_STUDENT_YEARLY"] = "price_student_yearly"
os.environ["STRIPE_PRICE_RESEARCHER_YEARLY"] = "price_researcher_yearly"
os.environ["STRIPE_PRICE_LAB_YEARLY"] = "price_lab_yearly"

from app.database import Base, engine, get_db  # noqa: E402
from app.dependencies import get_queue, get_storage, get_webhook_delivery_queue  # noqa: E402
from app.main import app  # noqa: E402
from app.config import get_settings  # noqa: E402
from app import rate_limit  # noqa: E402


class FakeStorage:
    def __init__(self) -> None:
        self.saved: list[dict[str, object]] = []

    def upload_fileobj(self, key: str, fileobj, content_type: str | None) -> None:
        self.saved.append(
            {
                "key": key,
                "content": fileobj.read(),
                "content_type": content_type,
            }
        )

    def download_file(self, key: str, destination_path: str) -> None:
        for item in self.saved:
            if item["key"] == key:
                with open(destination_path, "wb") as file:
                    file.write(item["content"])
                return
        raise FileNotFoundError(key)

    def delete_file(self, key: str) -> None:
        self.saved = [item for item in self.saved if item["key"] != key]


class FakeQueue:
    def __init__(self) -> None:
        self.pushed: list[str] = []

    def push_job(self, job_id: str) -> None:
        self.pushed.append(job_id)


class FakeWebhookQueue:
    def __init__(self) -> None:
        self.pushed: list[str] = []

    def push_delivery(self, delivery_id: str) -> None:
        self.pushed.append(delivery_id)


@pytest.fixture()
def fake_storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture()
def fake_queue() -> FakeQueue:
    return FakeQueue()


@pytest.fixture()
def fake_webhook_queue() -> FakeWebhookQueue:
    return FakeWebhookQueue()


@pytest.fixture()
def api_client(
    fake_storage: FakeStorage,
    fake_queue: FakeQueue,
    fake_webhook_queue: FakeWebhookQueue,
) -> Generator[TestClient, None, None]:
    get_settings.cache_clear()
    _reset_rate_limit_state()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_storage] = lambda: fake_storage
    app.dependency_overrides[get_queue] = lambda: fake_queue
    app.dependency_overrides[get_webhook_delivery_queue] = lambda: fake_webhook_queue
    with TestClient(app) as client:
        register = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "test-password-123", "name": "Test User"},
        )
        token = register.json()["accessToken"]
        client.headers.update({"authorization": f"Bearer {token}"})
        yield client
    app.dependency_overrides.clear()
    _reset_rate_limit_state()
    get_settings.cache_clear()


def _reset_rate_limit_state() -> None:
    rate_limit._fallback_counts.clear()
    rate_limit._redis_client = None
