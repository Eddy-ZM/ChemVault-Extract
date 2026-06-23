from __future__ import annotations

import re

from app.constants import ValidationStatus
from app.normalizers.base import NormalizationResult
from app.normalizers.text_normalizer import normalize_whitespace
from app.normalizers.unit_normalizer import normalize_unit

_MEASUREMENT_TYPE_MAP = {
    "h nmr": "1H NMR",
    "h-nmr": "1H NMR",
    "proton nmr": "1H NMR",
    "c nmr": "13C NMR",
    "13c nmr": "13C NMR",
    "c-nmr": "13C NMR",
    "cnmr": "13C NMR",
    "carbon nmr": "13C NMR",
    "carbon-nmr": "13C NMR",
    "ir": "IR",
    "infrared": "IR",
    "uv-vis": "UV-vis",
    "uv vis": "UV-vis",
    "uvvisible": "UV-vis",
    "mass spectrometry": "MS",
    "high resolution mass spectrometry": "HRMS",
    "liquid chromatography": "HPLC",
    "hplc": "HPLC",
    "hplc retention": "HPLC",
    "gas chromatography mass spectrometry": "GCMS",
    "uvvis": "UV-vis",
    "melting point": "melting_point",
    "boiling point": "boiling_point",
    "retention time": "retention_time",
    "hplc retention time": "HPLC",
}

_MEASUREMENT_TYPE_ALLOWED = {
    "1H NMR",
    "13C NMR",
    "IR",
    "MS",
    "HRMS",
    "HPLC",
    "GCMS",
    "UV-vis",
    "melting_point",
    "boiling_point",
    "retention_time",
    "absorbance",
    "pKa",
    "yield",
    "mass",
    "volume",
    "concentration",
    "temperature",
    "time",
    "other",
}

_KNOWN_MEASUREMENT_UNITS = {
    "%",
    "deg c",
    "deg. c",
    "degree c",
    "degree celcius",
    "molar",
    "millimolar",
    "mm",
    "m",
    "molarity",
    "minutes",
    "hours",
    "h",
    "min",
    "minute",
    "s",
    "sec",
    "second",
    "seconds",
    "k",
    "kelvin",
    "c",
    "celsius",
    "°c",
    "°C",
    "mole",
    "mol",
}

_KNOWN_CANONICAL_MEASUREMENT_UNITS = {
    "%",
    "M",
    "mM",
    "min",
    "h",
    "s",
    "°C",
    "K",
    "mol",
    "mmol",
    "g",
    "mg",
    "ug",
}


def normalize_measurement_record(item: dict, *, confidence: float | None = None) -> NormalizationResult:
    warnings: list[str] = []

    raw_measurement_type = normalize_whitespace(item.get("measurement_type"))
    raw_value = normalize_whitespace(item.get("value"))
    raw_unit = normalize_whitespace(item.get("unit"))
    raw_target = normalize_whitespace(item.get("target"))
    raw_raw_text = normalize_whitespace(item.get("raw_text"))

    status = ValidationStatus.VALID.value

    normalized_measurement_type = _normalize_measurement_type(raw_measurement_type)

    normalized_unit = normalize_unit(raw_unit)
    if raw_unit and normalized_unit is None:
        warnings.append("Could not normalize unit.")

    normalized_value = _normalize_numeric_or_range(raw_value)
    if raw_value and normalized_value is None:
        warnings.append("Could not normalize measurement value to numeric or recognized range.")
        status = ValidationStatus.NEEDS_REVIEW.value

    if not raw_measurement_type:
        status = ValidationStatus.INVALID.value
        warnings.append("Missing measurement_type.")
    elif raw_value is None:
        status = ValidationStatus.INVALID.value
        warnings.append("Missing measurement value.")
    elif raw_value and normalized_measurement_type == "other" and normalize_whitespace(raw_measurement_type) not in {"other", "other."}:
        warnings.append("Measurement type could not be normalized to a known enum.")
        status = ValidationStatus.NEEDS_REVIEW.value
    elif normalized_measurement_type not in _MEASUREMENT_TYPE_ALLOWED:
        status = ValidationStatus.NEEDS_REVIEW.value

    if confidence is not None and confidence < 0.75:
        warnings.append("Confidence is below 0.75.")
        if status == ValidationStatus.VALID.value:
            status = ValidationStatus.NEEDS_REVIEW.value

    if raw_unit and normalized_unit is None:
        if status == ValidationStatus.VALID.value:
            status = ValidationStatus.NEEDS_REVIEW.value

    if _is_uncertain_unit(raw_unit, normalized_unit):
        warnings.append(f"Unit '{raw_unit}' could not be confidently normalized.")
        if status == ValidationStatus.VALID.value:
            status = ValidationStatus.NEEDS_REVIEW.value

    normalized_conditions = item.get("conditions")

    return NormalizationResult(
        raw={
            "target": raw_target,
            "measurement_type": raw_measurement_type,
            "value": raw_value,
            "unit": raw_unit,
            "conditions": item.get("conditions"),
            "raw_text": raw_raw_text,
        },
        normalized={
            "measurementType": raw_measurement_type,
            "normalizedMeasurementType": normalized_measurement_type,
            "rawValue": raw_value,
            "normalizedValue": normalized_value,
            "rawUnit": raw_unit,
            "normalizedUnit": normalized_unit,
            "rawConditions": item.get("conditions"),
            "normalizedConditions": normalized_conditions,
            "target": raw_target,
            "rawText": raw_raw_text,
            "validationStatus": status,
            "validationWarnings": warnings,
        },
        validation_status=status,
        validation_warnings=warnings,
    )


def _is_uncertain_unit(raw_unit: str | None, normalized_unit: str | None) -> bool:
    if raw_unit is None:
        return False
    normalized = normalize_whitespace(raw_unit)
    if normalized is None:
        return False

    normalized_key = normalized.lower().strip()

    if normalized_unit is not None and normalized_unit in _KNOWN_CANONICAL_MEASUREMENT_UNITS:
        return False
    if normalized_key in _KNOWN_MEASUREMENT_UNITS:
        return False
    if normalized_unit is None:
        return False
    if normalized_unit.lower() == normalized_key:
        return True
    return normalized_unit.lower() != (normalize_unit(normalized_key) or normalized_key)


def _normalize_measurement_type(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if not normalized:
        return "other"

    # normalize repeated spaces and punctuation for reliable matching
    normalized = normalized.replace("_", " ").replace("  ", " ").strip()
    key = normalized.replace("  ", " ")

    if key in _MEASUREMENT_TYPE_MAP:
        return _MEASUREMENT_TYPE_MAP[key]

    if key == "uvvisible":
        return "UV-vis"
    if key.startswith("h nmr"):
        return "1H NMR"
    if key.startswith("c nmr"):
        return "13C NMR"

    return "other"



def _normalize_numeric_or_range(value: str | None) -> float | str | None:
    if value is None:
        return None

    normalized = normalize_whitespace(value)
    if normalized is None:
        return None

    plain = normalized.replace(",", ".")
    plain = plain.replace(" ", " ")
    plain = re.sub(r"\s+", " ", plain).strip()

    if "–" in plain:
        plain = plain.replace("–", "-")

    units_stripped = re.sub(r"[A-Za-z%°]+$", "", plain).strip()
    if units_stripped != plain:
        plain = units_stripped.strip()

    range_match = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\s*", plain)
    if range_match:
        return f"{range_match.group(1)}-{range_match.group(2)}"

    number_match = re.fullmatch(r"[+-]?(\d+(?:\.\d+)?)", plain)
    if number_match:
        try:
            return float(number_match.group(1))
        except ValueError:
            return None

    return None
