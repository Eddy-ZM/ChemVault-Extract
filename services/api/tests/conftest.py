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

from app.database import Base, engine, get_db  # noqa: E402
from app.dependencies import get_queue, get_storage  # noqa: E402
from app.main import app  # noqa: E402


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


class FakeQueue:
    def __init__(self) -> None:
        self.pushed: list[str] = []

    def push_job(self, job_id: str) -> None:
        self.pushed.append(job_id)


@pytest.fixture()
def fake_storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture()
def fake_queue() -> FakeQueue:
    return FakeQueue()


@pytest.fixture()
def api_client(fake_storage: FakeStorage, fake_queue: FakeQueue) -> Generator[TestClient, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_storage] = lambda: fake_storage
    app.dependency_overrides[get_queue] = lambda: fake_queue
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
