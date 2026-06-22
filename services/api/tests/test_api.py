import io

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
