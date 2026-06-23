from __future__ import annotations

from typing import Any, Iterator


class ChemVaultObject(dict):
    """Dict response wrapper with attribute access for SDK ergonomics."""

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__({key: wrap(value) for key, value in data.items()})

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def wrap(value: Any) -> Any:
    if isinstance(value, dict):
        return ChemVaultObject(value)
    if isinstance(value, list):
        return [wrap(item) for item in value]
    return value


def unwrap(value: Any) -> Any:
    if isinstance(value, ChemVaultObject):
        return {key: unwrap(item) for key, item in value.items()}
    if isinstance(value, list):
        return [unwrap(item) for item in value]
    return value


class Page(Iterator[Any]):
    def __init__(self, items: list[Any]) -> None:
        self.items = items
        self._index = 0

    def __iter__(self) -> "Page":
        return self

    def __next__(self) -> Any:
        if self._index >= len(self.items):
            raise StopIteration
        item = self.items[self._index]
        self._index += 1
        return item
