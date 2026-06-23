from __future__ import annotations


class ExtractionsResource:
    def __init__(self, client) -> None:
        self._client = client

    def estimate(self, document_id: str):
        return self._client.request("POST", f"/v1/documents/{document_id}/estimate")

    def extract(self, document_id: str, *, mode: str = "standard", model: str | None = None):
        return self._client.request(
            "POST",
            f"/v1/documents/{document_id}/extract",
            json={"mode": mode, "model": model},
        )

    def job(self, job_id: str):
        return self._client.request("GET", f"/v1/jobs/{job_id}")
