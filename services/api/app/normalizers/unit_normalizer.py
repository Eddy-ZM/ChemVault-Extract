from __future__ import annotations

from app.normalizers.text_normalizer import normalize_whitespace

_UNIT_MAP = {
    "minutes": "min",
    "minute": "min",
    "min": "min",
    "hours": "h",
    "hour": "h",
    "h": "h",
    "seconds": "s",
    "second": "s",
    "sec": "s",
    "s": "s",
    "percent": "%",
    "%": "%",
    "molar": "M",
    "millimolar": "mM",
    "mm": "mM",
    "m": "M",
    "celsius": "°C",
    "deg c": "°C",
    "deg. c": "°C",
    "degree c": "°C",
    "degree celcius": "°C",
    "°c": "°C",
    "c": "°C",
    "kelvin": "K",
    "k": "K",
}


def normalize_unit(value: str | None) -> str | None:
    normalized = normalize_whitespace(value)
    if not normalized:
        return None

    lowered = normalized.lower().strip()
    return _UNIT_MAP.get(lowered, normalized)
