from __future__ import annotations

import re

from app.constants import ValidationStatus
from app.normalizers.base import NormalizationResult
from app.normalizers.chemical_normalizer import normalize_chemical_record
from app.normalizers.text_normalizer import normalize_whitespace
from app.normalizers.unit_normalizer import normalize_unit
from app.validators.chemistry_validator import validate_temperature


def normalize_reaction_record(item: dict, *, confidence: float | None = None) -> NormalizationResult:
    warnings: list[str] = []

    raw_reactants = item.get("reactants") or []
    raw_products = item.get("products") or []
    raw_reagents = item.get("reagents") or []
    raw_solvents = item.get("solvents") or []
    raw_catalysts = item.get("catalysts") or []

    normalized_reactants, reactant_status, reactant_warnings = _normalize_chemical_list(raw_reactants, fallback_role="reactant")
    normalized_products, product_status, product_warnings = _normalize_chemical_list(raw_products, fallback_role="product")
    normalized_reagents, reagent_status, reagent_warnings = _normalize_chemical_list(raw_reagents, fallback_role="reagent")
    normalized_solvents, solvent_status, solvent_warnings = _normalize_chemical_list(raw_solvents, fallback_role="solvent")
    normalized_catalysts, catalyst_status, catalyst_warnings = _normalize_chemical_list(raw_catalysts, fallback_role="catalyst")

    warnings.extend(reactant_warnings)
    warnings.extend(product_warnings)
    warnings.extend(reagent_warnings)
    warnings.extend(solvent_warnings)
    warnings.extend(catalyst_warnings)

    raw_temperature = normalize_whitespace(item.get("temperature"))
    raw_time = normalize_whitespace(item.get("time"))
    raw_yield_value = normalize_whitespace(item.get("yield_value") or item.get("yield"))
    raw_yield_unit = normalize_whitespace(item.get("yield_unit"))

    normalized_temperature, temp_warning = validate_temperature(raw_temperature)
    if temp_warning and raw_temperature is not None and temp_warning != "Missing temperature.":
        warnings.append(temp_warning)

    normalized_time = _normalize_time(raw_time)
    if raw_time is not None and raw_time and _normalize_time(raw_time) != raw_time:
        # _normalize_time adds normalized unit/canonical form; warn only when not parseable.
        pass

    normalized_yield_value, normalized_yield_unit, yield_warning = _normalize_yield(
        raw_yield_value,
        raw_yield_unit,
        has_keyword=_contains_yield_prefix(raw_yield_value),
    )
    if yield_warning:
        warnings.append(yield_warning)

    status = ValidationStatus.VALID.value
    for value in (reactant_status, product_status, reagent_status, solvent_status, catalyst_status):
        if value == ValidationStatus.INVALID.value:
            status = ValidationStatus.INVALID.value
            break
        if value == ValidationStatus.NEEDS_REVIEW.value:
            status = ValidationStatus.NEEDS_REVIEW.value

    if not normalized_reactants and not normalized_products:
        status = ValidationStatus.INVALID.value
        warnings.append("Missing reactants and products.")

    if confidence is not None and confidence < 0.75:
        warnings.append("Confidence is below 0.75.")
        if status == ValidationStatus.VALID.value:
            status = ValidationStatus.NEEDS_REVIEW.value

    return NormalizationResult(
        raw={
            "reaction_name": normalize_whitespace(item.get("reaction_name")),
            "reactants": raw_reactants,
            "products": raw_products,
            "reagents": raw_reagents,
            "solvents": raw_solvents,
            "catalysts": raw_catalysts,
            "temperature": raw_temperature,
            "time": raw_time,
            "yield_value": raw_yield_value,
            "yield_unit": raw_yield_unit,
            "procedure": normalize_whitespace(item.get("procedure")),
            "atmosphere": normalize_whitespace(item.get("atmosphere")),
        },
        normalized={
            "reactionName": normalize_whitespace(item.get("reaction_name")),
            "rawReactants": raw_reactants,
            "normalizedReactants": normalized_reactants,
            "rawProducts": raw_products,
            "normalizedProducts": normalized_products,
            "rawReagents": raw_reagents,
            "normalizedReagents": normalized_reagents,
            "rawSolvents": raw_solvents,
            "normalizedSolvents": normalized_solvents,
            "rawCatalysts": raw_catalysts,
            "normalizedCatalysts": normalized_catalysts,
            "rawTemperature": raw_temperature,
            "normalizedTemperature": normalized_temperature,
            "rawTime": raw_time,
            "normalizedTime": normalized_time,
            "rawYieldValue": raw_yield_value,
            "normalizedYieldValue": normalized_yield_value,
            "rawYieldUnit": normalize_unit(raw_yield_unit),
            "normalizedYieldUnit": normalized_yield_unit,
            "procedure": normalize_whitespace(item.get("procedure")),
            "atmosphere": normalize_whitespace(item.get("atmosphere")),
            "validationStatus": status,
            "validationWarnings": warnings,
        },
        validation_status=status,
        validation_warnings=warnings,
    )



def _normalize_chemical_list(values: list, *, fallback_role: str | None = None) -> tuple[list[dict], str, list[str]]:
    normalized_items: list[dict] = []
    status = ValidationStatus.VALID.value
    warnings: list[str] = []

    for value in values:
        if isinstance(value, dict):
            item = dict(value)
            if fallback_role and not item.get("role"):
                item["role"] = fallback_role
            result = normalize_chemical_record(item)
            normalized_items.append(result.normalized)
            if result.validation_status == ValidationStatus.INVALID.value:
                status = ValidationStatus.INVALID.value
                warnings.extend(result.validation_warnings)
            elif result.validation_status == ValidationStatus.NEEDS_REVIEW.value and status == ValidationStatus.VALID.value:
                status = ValidationStatus.NEEDS_REVIEW.value
                warnings.extend(result.validation_warnings)
        else:
            status = ValidationStatus.NEEDS_REVIEW.value
            warnings.append("Non-dict chemical component detected.")

    return normalized_items, status, warnings



def _normalize_time(value: str | None) -> str | None:
    normalized = normalize_whitespace(value)
    if not normalized:
        return None

    lowered = normalized.lower()
    if lowered == "overnight":
        return "overnight"
    if lowered == "reflux":
        return "reflux"

    match = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z°%]+)?\s*$", lowered)
    if match is None:
        return normalized

    number = match.group(1)
    unit = normalize_unit(match.group(2))
    if unit is None:
        return normalized
    return f"{number} {unit}".strip()



def _normalize_yield(
    value: str | None,
    unit: str | None,
    *,
    has_keyword: bool = False,
) -> tuple[float | str | None, str | None, str | None]:
    normalized = normalize_whitespace(value)
    if not normalized:
        return None, normalize_unit(unit), None

    compact = normalized.lower()
    compact = compact.replace("%", " % ").replace("percent", " % ").strip().rstrip(":")
    if has_keyword:
        compact = compact.replace("yield:", "").replace("yield", "")
    compact = compact.replace("  ", " ").strip()

    normalized_unit = normalize_unit(unit)
    number_match = re.search(r"([0-9]+(?:\.[0-9]+)?)", compact)
    if not number_match:
        return None, normalized_unit, "Could not normalize yield value."

    try:
        number = float(number_match.group(1))
    except ValueError:
        return None, normalized_unit, "Could not normalize yield value."

    unit_from_text = "" if normalized_unit is None else normalized_unit
    if "% " in compact or compact.endswith("%") or " %" in compact:
        unit_from_text = "%"

    if unit_from_text == "%":
        if number <= 1:
            return round(number * 100, 10), "%", None
        return number, "%", None

    if has_keyword:
        if number <= 1:
            return round(number * 100, 10), "%", None
        if number <= 100:
            return number, "%", None

    if normalized_unit is None and number <= 1:
        return round(number * 100, 10), "%", None

    if normalized_unit is None and number <= 100:
        return number, "%", None

    return number, normalized_unit, None


def _contains_yield_prefix(value: str | None) -> bool:
    if not value:
        return False
    return "yield" in normalize_whitespace(value).lower()
