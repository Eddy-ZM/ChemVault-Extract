from __future__ import annotations

from typing import Any


class DocumentsResource:
    def __init__(self, client) -> None:
        self._client = client

    def upload(
        self,
        *,
        project_id: str,
        file_path: str,
        auto_parse: bool = True,
        auto_extract: bool = False,
    ):
        return self._client.upload_file(
            file_path,
            project_id=project_id,
            auto_parse=auto_parse,
            auto_extract=auto_extract,
        )

    def list(self, **params: Any):
        return self._client.request("GET", "/v1/documents", params=params)

    def retrieve(self, document_id: str):
        return self._client.request("GET", f"/v1/documents/{document_id}")

    def status(self, document_id: str):
        return self._client.request("GET", f"/v1/documents/{document_id}/status")

    def chunks(self, document_id: str):
        return self._client.request("GET", f"/v1/documents/{document_id}/chunks")

    def estimate(self, document_id: str):
        return self._client.request("POST", f"/v1/documents/{document_id}/estimate")

    def extract(self, document_id: str, *, mode: str = "standard", model: str | None = None):
        return self._client.request(
            "POST",
            f"/v1/documents/{document_id}/extract",
            json={"mode": mode, "model": model},
        )

    def records(self, document_id: str, *, include_unapproved: bool = False):
        return self._client.request(
            "GET",
            f"/v1/documents/{document_id}/records",
            params={"include_unapproved": include_unapproved},
        )
