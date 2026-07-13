from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from chemvault.errors import ChemVaultError
from chemvault.models import wrap
from chemvault.resources.documents import DocumentsResource
from chemvault.resources.exports import ExportsResource
from chemvault.resources.extractions import ExtractionsResource
from chemvault.resources.projects import ProjectsResource
from chemvault.resources.records import RecordsResource


class ChemVault:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError(
                "ChemVault Extract API is retired. Provide base_url only for an explicitly maintained "
                "self-hosted legacy API; use ChemVault Lab for current workflows."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = http_client or httpx.Client(timeout=timeout)
        self.projects = ProjectsResource(self)
        self.documents = DocumentsResource(self)
        self.extractions = ExtractionsResource(self)
        self.records = RecordsResource(self)
        self.exports = ExportsResource(self)

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = self._client.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            json=json,
            params=_clean(params),
            files=files,
            data=_clean(data),
        )
        return self._handle_response(response)

    def upload_file(self, path: str, *, project_id: str, auto_parse: bool = True, auto_extract: bool = False) -> Any:
        file_path = Path(path)
        with file_path.open("rb") as file_obj:
            files = {"file": (file_path.name, file_obj)}
            data = {
                "project_id": project_id,
                "auto_parse": str(auto_parse).lower(),
                "auto_extract": str(auto_extract).lower(),
            }
            return self.request("POST", "/v1/documents", files=files, data=data)

    def _handle_response(self, response: httpx.Response) -> Any:
        request_id = response.headers.get("x-request-id")
        if 200 <= response.status_code < 300:
            if not response.content:
                return None
            return wrap(response.json())
        try:
            payload = response.json()
        except ValueError as exc:
            raise ChemVaultError(
                response.text or f"ChemVault API request failed with {response.status_code}",
                status_code=response.status_code,
                request_id=request_id,
            ) from exc
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict):
            raise ChemVaultError(
                error.get("message") or "ChemVault API request failed.",
                code=error.get("code"),
                status_code=response.status_code,
                details=error.get("details") or {},
                request_id=request_id,
            )
        raise ChemVaultError(
            payload.get("detail") if isinstance(payload, dict) else "ChemVault API request failed.",
            status_code=response.status_code,
            request_id=request_id,
        )


def _clean(values: dict[str, Any] | None) -> dict[str, Any] | None:
    if values is None:
        return None
    return {key: value for key, value in values.items() if value is not None}
