from __future__ import annotations

from typing import Protocol


class QueueBackend(Protocol):
    def push(self, message: str) -> None: ...

    def pop(self, timeout_seconds: int = 5) -> str | None: ...
