from __future__ import annotations

from typing import Any


class RecordsResource:
    def __init__(self, client) -> None:
        self._client = client

    def document_records(self, document_id: str, *, include_unapproved: bool = False):
        return self._client.request(
            "GET",
            f"/v1/documents/{document_id}/records",
            params={"include_unapproved": include_unapproved},
        )

    def chemicals(self, **filters: Any):
        return self._client.request("GET", "/v1/records/chemicals", params=filters)

    def reactions(self, **filters: Any):
        return self._client.request("GET", "/v1/records/reactions", params=filters)

    def measurements(self, **filters: Any):
        return self._client.request("GET", "/v1/records/measurements", params=filters)

    def search(self, query: str, **filters: Any):
        return self._client.request("GET", "/v1/search", params={"q": query, **filters})
