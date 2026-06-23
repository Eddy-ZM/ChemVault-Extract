import httpx
import pytest

from app.normalizers.chemical_normalizer import normalize_chemical_record
from app.normalizers.measurement_normalizer import normalize_measurement_record
from app.normalizers.pubchem_enricher import _CACHE
from app.normalizers.reaction_normalizer import normalize_reaction_record


def test_chemical_abbreviation_normalization_to_standard_form():
    result = normalize_chemical_record(
        {
            "name": "EtOH",
            "role": "solvent",
            "evidence": {"chunk_id": "chunk-1", "page": 1, "quote": "dissolved in EtOH"},
        },
        confidence=0.9,
    )

    assert result.normalized["rawName"] == "EtOH"
    assert result.normalized["normalizedName"] == "ethanol"
    assert result.normalized["normalizedRole"] == "solvent"
    assert result.validation_status in {"valid", "needs_review"}


def test_chemical_other_abbreviations_are_annotated_when_not_found():
    result = normalize_chemical_record(
        {
            "name": "NaOCl",
            "evidence": {"chunk_id": "chunk-1", "page": 1, "quote": "NaOCl was used."},
        },
        confidence=0.9,
    )

    assert result.normalized["normalizedName"] == "sodium hypochlorite"
    assert result.normalized["enrichmentStatus"] in {"not_found", "found", "error"}


def test_reaction_yield_normalization_supports_percent_and_keyword_variants():
    result = normalize_reaction_record(
        {
            "reaction_name": "Test",
            "yield_value": "82%",
            "yield_unit": "%",
            "temperature": "rt",
            "evidence": {"chunk_id": "chunk-1", "page": 1, "quote": "yield 82%"},
        },
        confidence=0.99,
    )

    assert result.normalized["normalizedYieldValue"] == 82
    assert result.normalized["normalizedYieldUnit"] == "%"
    assert result.normalized["normalizedTemperature"] == "room temperature"


def test_measurement_type_normalization_for_proton_nmr():
    result = normalize_measurement_record(
        {
            "measurement_type": "proton NMR",
            "value": "7.26",
            "unit": "ppm",
            "target": "Product",
            "raw_text": "1H NMR (400 MHz, CDCl3): ...",
            "evidence": {"chunk_id": "chunk-1", "page": 1, "quote": "1H NMR"},
        },
        confidence=0.99,
    )

    assert result.normalized["normalizedMeasurementType"] == "1H NMR"
    assert result.normalized["normalizedConditions"] is None


def test_reaction_temperature_room_temperature_is_normalized():
    assert normalize_reaction_record({"temperature": "room temp", "evidence": {"chunk_id": "chunk-1", "page": 1, "quote": "rt"}})[
        "normalized"
    ]["normalizedTemperature"] == "room temperature"


@pytest.mark.parametrize(
    "value",
    [
        "82%",
        "82 percent",
        "0.82",
        "yield: 82",
    ],
)
def test_reaction_yield_inputs_all_map_to_percent(value):
    result = normalize_reaction_record(
        {
            "yield_value": value,
            "evidence": {"chunk_id": "chunk-1", "page": 1, "quote": "yield"},
        },
        confidence=0.9,
    )

    assert result.normalized["normalizedYieldValue"] == 82
    assert result.normalized["normalizedYieldUnit"] == "%"


def test_pubchem_enrichment_error_does_not_crash_normalization(monkeypatch):
    def raise_request(*_args, **_kwargs):
        raise httpx.RequestError("network down", request=httpx.Request("GET", "https://example.com"))

    monkeypatch.setattr("app.normalizers.pubchem_enricher.httpx.get", raise_request)
    _CACHE.clear()

    result = normalize_chemical_record(
        {
            "name": "Benzene",
            "evidence": {"chunk_id": "chunk-1", "page": 1, "quote": "ben"},
        },
        confidence=0.95,
    )

    assert result.normalized["enrichmentStatus"] == "error"
    assert any("PubChem request failed" in warning for warning in result.validation_warnings)
    assert result.validation_status in {"valid", "needs_review", "invalid"}
