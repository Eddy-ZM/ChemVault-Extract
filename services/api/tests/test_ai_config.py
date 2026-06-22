from app.config.ai import AISettings, estimate_tokens, select_chunks_for_ai
from app.extractors.base import to_openai_strict_json_schema
from app.extractors.schemas import MeasurementExtraction, MeasurementExtractionOutput
from app.models import DocumentChunk


def test_select_chunks_for_ai_prioritizes_sections_excludes_references_and_truncates():
    settings = AISettings(
        provider="openai",
        default_model="gpt-4.1-mini",
        fallback_model="gpt-5.5",
        max_chunks_per_document=2,
        max_chunk_chars=10,
        enable_fallback_model=False,
        estimated_input_token_ratio=0.25,
        monthly_free_file_limit=10,
        openai_api_key="test-key",
    )
    chunks = [
        DocumentChunk(
            id="intro",
            document_id="doc",
            chunk_index=0,
            section="Introduction",
            page_start=1,
            page_end=1,
            text="intro text",
        ),
        DocumentChunk(
            id="refs",
            document_id="doc",
            chunk_index=1,
            section="References and Notes",
            page_start=9,
            page_end=9,
            text="reference text",
        ),
        DocumentChunk(
            id="exp",
            document_id="doc",
            chunk_index=2,
            section="Experimental",
            page_start=2,
            page_end=2,
            text="x" * 25,
        ),
        DocumentChunk(
            id="results",
            document_id="doc",
            chunk_index=3,
            section="Results",
            page_start=3,
            page_end=3,
            text="result text",
        ),
    ]

    selected = select_chunks_for_ai(chunks, settings)

    assert [chunk.id for chunk in selected] == ["exp", "results"]
    assert selected[0].text == "x" * 10
    assert selected[0].metadata == {"truncated": True, "original_chars": 25, "used_chars": 10}
    assert estimate_tokens("abcd", 0.25) == 1


def test_openai_json_schema_is_strict_for_nested_models():
    schema = to_openai_strict_json_schema(MeasurementExtractionOutput.model_json_schema())
    measurement_schema = schema["$defs"]["MeasurementExtraction"]
    condition_schema = schema["$defs"]["MeasurementCondition"]

    assert schema["additionalProperties"] is False
    assert schema["required"] == ["items"]
    assert measurement_schema["additionalProperties"] is False
    assert set(measurement_schema["required"]) == set(measurement_schema["properties"].keys())
    assert "default" not in measurement_schema["properties"]["target"]
    assert condition_schema["additionalProperties"] is False
    assert set(condition_schema["required"]) == {"name", "value", "unit"}


def test_measurement_conditions_accept_legacy_dict_shape():
    measurement = MeasurementExtraction.model_validate(
        {
            "measurement_type": "HPLC",
            "conditions": {"column": "C18", "flow_rate": {"value": "1.0", "unit": "mL/min"}},
            "raw_text": "HPLC retention time was 3.2 min.",
            "evidence": {
                "document_id": "doc",
                "chunk_id": "chunk",
                "page": 1,
                "section": "Experimental",
                "quote": "HPLC retention time was 3.2 min.",
            },
        }
    )

    assert measurement.conditions[0].name == "column"
    assert measurement.conditions[0].value == "C18"
    assert measurement.conditions[1].name == "flow_rate"
