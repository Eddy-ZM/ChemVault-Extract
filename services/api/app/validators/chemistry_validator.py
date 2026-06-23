from __future__ import annotations

import re

from app.extractors.schemas import MeasurementType

MEASUREMENT_TYPES = {value for value in MeasurementType.__args__}


def normalize_confidence(value: float | int | None) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def validate_measurement_type(value: str | None) -> bool:
    return value in MEASUREMENT_TYPES if value else False


def validate_and_extract_yield(value: str | None) -> tuple[float | str | None, str | None, str | None]:
    if not value:
        return None, None, None

    normalized = str(value).strip().lower()
    if normalized in {"yield", "yield:", "yield value"}:
        return None, None, None

    compact = re.sub(r"[^0-9.%a-zA-Z ]", " ", normalized)
    compact = compact.replace("percent", "%").replace("  ", " ").strip()

    unit: str | None = None
    if "%" in compact:
        unit = "%"
    elif compact.endswith("%"):
        unit = "%"

    number_match = re.search(r"\d+(?:\.\d+)?", compact)
    if not number_match:
        return None, unit, "Could not parse yield numeric value."

    try:
        number = float(number_match.group(0))
    except ValueError:
        return None, unit, "Could not parse yield numeric value."

    # Accept fraction-style yields.
    if unit is None and number <= 1:
        number *= 100
        unit = "%"
        return number, unit, None

    if unit == "%" and number > 1 and number <= 100:
        return number, unit, None

    if number > 100 and unit is None:
        return number, unit, "Yield appears to be a percentage over 100."

    return number, unit or None, None


def validate_temperature(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, "Missing temperature."

    compact = str(value).strip().lower()
    cleaned = compact.replace("deg", "").replace("degree", "").replace("°", "").strip()

    if compact in {"rt", "room temp", "room temperature"}:
        return "room temperature", None

    if compact == "reflux":
        return "reflux", None

    celsius_match = re.match(r"^(\d+(?:\.\d+)?)\s*c(el(sius)?)?$", cleaned)
    if celsius_match:
        return f"{celsius_match.group(1)} °C", None

    kelvin_match = re.match(r"^(\d+(?:\.\d+)?)\s*k(elvin)?$", cleaned)
    if kelvin_match:
        return f"{kelvin_match.group(1)} K", None

    generic_temperature_match = re.match(r"^(\d+(?:\.\d+)?)(?:\s*(?:c|f|k))$", cleaned)
    if generic_temperature_match:
        unit = cleaned[len(generic_temperature_match.group(1)) :].strip()
        if unit == "c":
            return f"{generic_temperature_match.group(1)} °C", None
        if unit == "k":
            return f"{generic_temperature_match.group(1)} K", None
        if unit == "f":
            return f"{generic_temperature_match.group(1)} °F", None

    return compact, None


def validate_time(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, "Missing reaction time."

    compact = str(value).strip().lower()
    if compact == "overnight":
        return compact, None

    return compact, None
