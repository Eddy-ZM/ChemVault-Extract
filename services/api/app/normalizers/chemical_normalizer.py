from __future__ import annotations

from app.constants import ValidationStatus
from app.normalizers.base import NormalizationResult
from app.normalizers.pubchem_enricher import enrich_compound
from app.normalizers.rdkit_validator import validate_smiles
from app.normalizers.text_normalizer import normalize_whitespace
from app.normalizers.unit_normalizer import normalize_unit

_NAME_ABBREVIATIONS = {
    "etoh": "ethanol",
    "meoh": "methanol",
    "dcm": "dichloromethane",
    "ch2cl2": "dichloromethane",
    "thf": "tetrahydrofuran",
    "dmf": "n,n-dimethylformamide",
    "dmso": "dimethyl sulfoxide",
    "etoac": "ethyl acetate",
    "hcl": "hydrochloric acid",
    "naoh": "sodium hydroxide",
    "koh": "potassium hydroxide",
    "na2so4": "sodium sulfate",
    "mgso4": "magnesium sulfate",
    "naocl": "sodium hypochlorite",
}

_ROLE_MAP = {
    "reactant": "reactant",
    "substrate": "reactant",
    "starting material": "reactant",
    "product": "product",
    "reactants": "reactant",
    "reagent": "reagent",
    "oxidant": "reagent",
    "reducing agent": "reagent",
    "solvent": "solvent",
    "solvents": "solvent",
    "catalyst": "catalyst",
    "analyte": "analyte",
    "standard": "standard",
    "unknown": "unknown",
}

_KNOWN_CHEMICAL_UNITS = {
    "%",
    "m",
    "g",
    "kg",
    "mg",
    "ug",
    "μg",
    "ug",
    "ml",
    "l",
    "mol",
    "mmol",
    "umol",
    "μmol",
    "cm3",
    "m3",
    "µL",
    "ul",
    "ml",
    "l",
    "mol/l",
    "mmol/l",
    "eq",
    "eq.",
    "equiv",
    "equivalents",
    "molar",
    "millimolar",
    "mM",
    "M",
}


def normalize_chemical_record(item: dict, *, confidence: float | None = None) -> NormalizationResult:
    warnings: list[str] = []

    raw_name = normalize_whitespace(item.get("name"))
    raw_formula = normalize_whitespace(item.get("formula"))
    raw_smiles = normalize_whitespace(item.get("smiles"))
    raw_inchi = normalize_whitespace(item.get("inchi"))
    raw_inchi_key = normalize_whitespace(item.get("inchiKey") or item.get("inchi_key"))
    raw_cas = normalize_whitespace(item.get("cas"))
    raw_role = normalize_whitespace(item.get("role") or item.get("entityType") or item.get("entity_type"))
    raw_amount = normalize_whitespace(item.get("amount"))
    raw_unit = normalize_whitespace(item.get("unit"))

    normalized_name = _normalize_name(raw_name)
    normalized_role = _normalize_role(raw_role, warnings)
    normalized_formula = _normalize_formula(raw_formula)

    pubchem_status, pubchem_data, pubchem_warnings = _enrich(normalized_name)
    warnings.extend(pubchem_warnings)

    pubchem_formula = pubchem_data.get("molecularFormula") if pubchem_data else None
    normalized_formula = _normalize_formula(pubchem_formula) if pubchem_formula else normalized_formula
    inchi_value = raw_inchi or (pubchem_data.get("inchi") if pubchem_data else None)
    inchi_key_value = raw_inchi_key or (pubchem_data.get("inchiKey") if pubchem_data else None)

    canonical_smiles = raw_smiles
    if raw_smiles and pubchem_data and pubchem_data.get("canonicalSmiles"):
        canonical_smiles = normalize_whitespace(pubchem_data.get("canonicalSmiles"))

    rdkit_result = validate_smiles(canonical_smiles)
    rdkit_valid = rdkit_result[0]
    rdkit_canonical = rdkit_result[1]
    rdkit_warnings = rdkit_result[2]
    warnings.extend(rdkit_warnings)
    if rdkit_canonical is not None:
        canonical_smiles = rdkit_canonical

    status = ValidationStatus.VALID.value
    normalized_unit = normalize_unit(raw_unit)
    if raw_unit:
        normalized_unit_normalized = (normalized_unit or "").strip().lower()
        if normalized_unit_normalized and normalized_unit_normalized not in {u.lower() for u in _KNOWN_CHEMICAL_UNITS}:
            warnings.append("Could not confidently normalize unit.")
            status = ValidationStatus.NEEDS_REVIEW.value

    if not raw_name:
        status = ValidationStatus.INVALID.value
        warnings.append("Raw name is missing.")
    elif not normalized_name:
        status = ValidationStatus.INVALID.value

    if rdkit_valid is False:
        status = ValidationStatus.NEEDS_REVIEW.value

    if confidence is not None and confidence < 0.75:
        warnings.append("Confidence is below 0.75.")
        if status == ValidationStatus.VALID.value:
            status = ValidationStatus.NEEDS_REVIEW.value

    if normalized_role == "unknown":
        if status == ValidationStatus.VALID.value:
            status = ValidationStatus.NEEDS_REVIEW.value

    if status == ValidationStatus.VALID.value and not normalized_name and raw_name:
        status = ValidationStatus.NEEDS_REVIEW.value

    if pubchem_status == "not_found":
        warnings.append("PubChem result not found.")
        status = ValidationStatus.NEEDS_REVIEW.value

    if pubchem_status == "error":
        warnings.append("PubChem result lookup returned an error.")
        if status == ValidationStatus.VALID.value:
            status = ValidationStatus.NEEDS_REVIEW.value

    enrichment_status = pubchem_status
    enrichment_source = "pubchem" if pubchem_status else None

    if raw_unit and normalized_unit is None:
        status = ValidationStatus.NEEDS_REVIEW.value

    normalized_value = {
        "rawName": raw_name,
        "normalizedName": normalized_name,
        "formula": raw_formula,
        "normalizedFormula": normalized_formula,
        "smiles": raw_smiles,
        "canonicalSmiles": canonical_smiles,
        "inchi": inchi_value,
        "inchiKey": inchi_key_value,
        "cas": raw_cas,
        "role": raw_role,
        "normalizedRole": normalized_role,
        "amount": raw_amount,
        "normalizedAmount": raw_amount,
        "unit": raw_unit,
        "normalizedUnit": normalized_unit,
        "validationStatus": status,
        "validationWarnings": warnings,
        "enrichmentStatus": enrichment_status,
        "enrichmentSource": enrichment_source,
        "pubchemCid": pubchem_data.get("pubchemCid") if pubchem_data else None,
        "molecularFormula": pubchem_data.get("molecularFormula") if pubchem_data else None,
        "molecularWeight": pubchem_data.get("molecularWeight") if pubchem_data else None,
        "rdkitAvailable": rdkit_valid is not None,
    }

    raw_payload = {
        "name": raw_name,
        "formula": raw_formula,
        "smiles": raw_smiles,
        "inchi": raw_inchi,
        "inchiKey": raw_inchi_key,
        "cas": raw_cas,
        "role": raw_role,
        "amount": raw_amount,
        "unit": raw_unit,
    }

    return NormalizationResult(raw=raw_payload, normalized=normalized_value, validation_status=status, validation_warnings=warnings)



def _normalize_name(value: str | None) -> str | None:
    if not value:
        return None

    normalized = " ".join(value.strip().split())
    if not normalized:
        return None

    lowered = normalized.lower()
    lowered_no_space = lowered.replace(" ", "")
    if lowered_no_space in _NAME_ABBREVIATIONS:
        return _NAME_ABBREVIATIONS[lowered_no_space]

    mapped = _NAME_ABBREVIATIONS.get(lowered)
    if mapped:
        return mapped

    return normalized.lower()



def _normalize_role(value: str | None, warnings: list[str]) -> str:
    if not value:
        warnings.append("Role is missing.")
        return "unknown"

    normalized = value.strip().lower()
    role = _ROLE_MAP.get(normalized)
    if role is None:
        warnings.append("Role is not recognized; normalizedRole set to unknown.")
        return "unknown"
    return role



def _normalize_formula(value: str | None) -> str | None:
    if not value:
        return None
    normalized = str(value).replace(" ", "").strip() or None
    return normalized



def _enrich(name: str | None) -> tuple[str, dict, list[str]]:
    if not name:
        return "invalid", {}, ["No compound name provided."]

    result = enrich_compound(name)
    if result.status == "found":
        payload = dict(result.data or {})
        return "enriched", payload, result.warnings
    if result.status == "not_found":
        return "not_found", {}, ["PubChem returned no results."] + result.warnings
    return "error", {}, ["PubChem enrichment error."] + result.warnings
