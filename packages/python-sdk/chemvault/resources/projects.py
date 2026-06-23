from __future__ import annotations

from typing import Any


class ProjectsResource:
    def __init__(self, client) -> None:
        self._client = client

    def list(self, **params: Any):
        return self._client.request("GET", "/v1/projects", params=params)

    def create(self, *, name: str, workspace_id: str | None = None):
        payload = {"name": name}
        if workspace_id:
            payload["workspace_id"] = workspace_id
        return self._client.request("POST", "/v1/projects", json=payload)

    def retrieve(self, project_id: str):
        return self._client.request("GET", f"/v1/projects/{project_id}")
