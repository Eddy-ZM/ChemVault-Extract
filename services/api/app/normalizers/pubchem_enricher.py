from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from urllib.parse import quote_plus

import httpx

from app.config import get_settings
from app.normalizers.text_normalizer import normalize_whitespace


def _enrichment_cache_key(name: str) -> str:
    return normalize_whitespace(name).lower() if name else ""


@dataclass
class PubChemResult:
    status: str
    data: dict | None
    warnings: list[str]


_CACHE: dict[str, tuple[float, PubChemResult]] = {}


def enrich_compound(name: str) -> PubChemResult:
    settings = get_settings()
    normalized = normalize_whitespace(name)
    if not normalized:
        return PubChemResult(status="invalid", data=None, warnings=["No compound name provided."])

    cache_key = _enrichment_cache_key(normalized)
    now = monotonic()
    cached = _CACHE.get(cache_key)
    if cached is not None and cached[0] + settings.pubchem_cache_ttl_seconds >= now:
        return cached[1]

    url = f"{settings.pubchem_base_url.rstrip('/')}/rest/pug/compound/name/{quote_plus(normalized)}/property/MolecularFormula,MolecularWeight,InChI,InChIKey,CanonicalSMILES/JSON"
    try:
        response = httpx.get(url, timeout=settings.pubchem_timeout_seconds)
    except httpx.RequestError as exc:  # noqa: BLE001
        result = PubChemResult(
            status="error",
            data=None,
            warnings=[f"PubChem request failed: {exc}"],
        )
        _CACHE[cache_key] = (now, result)
        return result

    if response.status_code == 404:
        result = PubChemResult(status="not_found", data=None, warnings=["No PubChem compound found."])
        _CACHE[cache_key] = (now, result)
        return result

    if response.status_code >= 400:
        result = PubChemResult(
            status="error",
            data=None,
            warnings=[f"PubChem API returned status {response.status_code}."],
        )
        _CACHE[cache_key] = (now, result)
        return result

    try:
        payload = response.json()
    except ValueError:
        result = PubChemResult(status="error", data=None, warnings=["PubChem returned invalid JSON payload."])
        _CACHE[cache_key] = (now, result)
        return result

    properties = payload.get("PropertyTable", {}).get("Properties") if isinstance(payload, dict) else None
    if not properties:
        result = PubChemResult(status="not_found", data=None, warnings=["No PubChem compound properties found."])
        _CACHE[cache_key] = (now, result)
        return result

    record = properties[0] if properties else {}
    if not isinstance(record, dict):
        result = PubChemResult(
            status="error",
            data=None,
            warnings=["Unexpected PubChem payload format for compound properties."],
        )
        _CACHE[cache_key] = (now, result)
        return result

    result = PubChemResult(
        status="found",
        data={
            "pubchemCid": record.get("CID"),
            "canonicalSmiles": record.get("CanonicalSMILES"),
            "inchi": record.get("InChI"),
            "inchiKey": record.get("InChIKey"),
            "molecularFormula": record.get("MolecularFormula"),
            "molecularWeight": record.get("MolecularWeight"),
        },
        warnings=[],
    )
    _CACHE[cache_key] = (now, result)
    return result
