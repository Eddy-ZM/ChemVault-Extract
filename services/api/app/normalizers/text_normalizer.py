from __future__ import annotations

import re


def normalize_whitespace(value: str | None) -> str | None:
    if not value:
        return None
    collapsed = re.sub(r"\s+", " ", str(value)).strip()
    return collapsed or None


def normalize_lower_strip(value: str | None) -> str | None:
    if not value:
        return None
    return normalize_whitespace(value).lower()


def normalize_title(value: str | None) -> str | None:
    normalized = normalize_whitespace(value)
    if normalized is None:
        return None
    return normalized.strip().title()
