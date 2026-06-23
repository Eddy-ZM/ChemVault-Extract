from __future__ import annotations

from pathlib import Path
from typing import Any


class ExportsResource:
    def __init__(self, client) -> None:
        self._client = client

    def create(self, *, project_id: str, export_format: str = "json"):
        return self._client.request(
            "POST",
            "/v1/exports",
            json={"projectId": project_id, "exportFormat": export_format},
        )

    def list(self, **params: Any):
        return self._client.request("GET", "/v1/exports", params=params)

    def retrieve(self, export_id: str):
        return self._client.request("GET", f"/v1/exports/{export_id}")

    def download(self, export_id: str, output_path: str | None = None):
        result = self._client.request("GET", f"/v1/exports/{export_id}/download")
        if output_path and result.get("content"):
            Path(output_path).write_bytes(result["content"])
        return result
