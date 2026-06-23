from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from chemvault import ChemVault
from chemvault.errors import ChemVaultError


def test_projects_list_sends_api_key_auth() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://api.test/v1/projects"
        assert request.headers["authorization"] == "Bearer cv_test_secret"
        return httpx.Response(200, json=[{"id": "proj_1", "name": "Organic synthesis"}])

    client = ChemVault(
        api_key="cv_test_secret",
        base_url="https://api.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    projects = client.projects.list()

    assert projects[0].id == "proj_1"


def test_documents_upload_sends_multipart_form_data(tmp_path: Path) -> None:
    sample = tmp_path / "notes.txt"
    sample.write_text("hello", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://api.test/v1/documents"
        assert request.headers["authorization"] == "Bearer cv_test_secret"
        assert "multipart/form-data" in request.headers["content-type"]
        body = request.read()
        assert b'name="project_id"' in body
        assert b"proj_1" in body
        assert b'filename="notes.txt"' in body
        return httpx.Response(201, json={"document_id": "doc_1", "status": "uploaded"})

    client = ChemVault(
        api_key="cv_test_secret",
        base_url="https://api.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    document = client.documents.upload(project_id="proj_1", file_path=str(sample))

    assert document.document_id == "doc_1"


def test_api_error_payload_becomes_chemvault_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            headers={"x-request-id": "req_123"},
            json={
                "error": {
                    "code": "insufficient_scope",
                    "message": "Scope missing.",
                    "details": {"scope": "projects:read"},
                }
            },
        )

    client = ChemVault(
        api_key="cv_test_secret",
        base_url="https://api.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ChemVaultError) as raised:
        client.projects.list()

    assert raised.value.code == "insufficient_scope"
    assert raised.value.status_code == 403
    assert raised.value.request_id == "req_123"
