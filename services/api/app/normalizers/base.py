from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NormalizationResult:
    raw: dict[str, Any]
    normalized: dict[str, Any]
    validation_status: str
    validation_warnings: list[str] = field(default_factory=list)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


def combine_statuses(*statuses: str) -> str:
    normalized = "valid"
    for status in statuses:
        if status == "invalid":
            return "invalid"
        if status == "needs_review":
            normalized = "needs_review"
    return normalized
