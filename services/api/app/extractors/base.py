from dataclasses import dataclass
import copy
import json
from typing import Any

from app.config.ai import SelectedChunk
from app.models import DocumentChunk


@dataclass(slots=True)
class ExtractionResult:
    extractor_type: str
    model_name: str
    input_chunk_ids: list[str]
    selected_chunk_ids: list[str]
    provider: str
    input_tokens_estimated: int
    output_tokens_estimated: int
    estimated_cost_usd: float
    raw_output: dict | list | str | None
    parsed_output: dict | list | None
    status: str
    message: str | None = None
    error: str | None = None


class BaseStructuredExtractor:
    extractor_type = "base"
    schema_name = "extraction"
    output_model: Any = None
    preferred_sections: tuple[str, ...] = ()
    max_chunks = 6

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def select_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        preferred = [
            chunk
            for chunk in chunks
            if chunk.section
            and any(section.casefold() in chunk.section.casefold() for section in self.preferred_sections)
        ]
        selected = preferred or chunks
        return selected[: self.max_chunks]

    def extract(self, document_id: str, chunks: list[DocumentChunk]) -> ExtractionResult:
        selected = self.select_chunks(chunks)
        return ExtractionResult(
            extractor_type=self.extractor_type,
            model_name=self.model_name,
            input_chunk_ids=[chunk.id for chunk in selected],
            selected_chunk_ids=[chunk.id for chunk in selected],
            provider="none",
            input_tokens_estimated=0,
            output_tokens_estimated=0,
            estimated_cost_usd=0,
            raw_output=None,
            parsed_output={"items": []},
            status="skipped",
            message="No AI provider configured; extraction skipped without generating records.",
        )

    def json_schema(self) -> dict[str, Any]:
        if self.output_model is None:
            return {
                "type": "object",
                "properties": {"items": {"type": "array"}},
                "required": ["items"],
                "additionalProperties": False,
            }
        return to_openai_strict_json_schema(self.output_model.model_json_schema())

    def validate_output(self, parsed_output: dict) -> dict:
        if self.output_model is None:
            return parsed_output
        return self.output_model.model_validate(parsed_output).model_dump(mode="json")

    def build_prompt(self, *, document_id: str, selected_chunks: list[SelectedChunk]) -> str:
        chunk_payload = [
            {
                "chunk_id": chunk.id,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "section": chunk.section,
                "text": chunk.text,
            }
            for chunk in selected_chunks
        ]
        return (
            f"Document ID: {document_id}\n"
            f"Extractor type: {self.extractor_type}\n"
            "Use only the selected chunks below. Do not use references or outside knowledge.\n"
            "Return JSON that exactly matches the schema.\n\n"
            f"Selected chunks:\n{json.dumps(chunk_payload, ensure_ascii=True)}"
        )

    def skipped_result(
        self,
        *,
        selected_chunks: list[SelectedChunk],
        provider: str,
        input_tokens_estimated: int,
        output_tokens_estimated: int,
        estimated_cost_usd: float,
        message: str,
    ) -> ExtractionResult:
        selected_chunk_ids = [chunk.id for chunk in selected_chunks]
        return ExtractionResult(
            extractor_type=self.extractor_type,
            model_name=self.model_name,
            input_chunk_ids=selected_chunk_ids,
            selected_chunk_ids=selected_chunk_ids,
            provider=provider,
            input_tokens_estimated=input_tokens_estimated,
            output_tokens_estimated=output_tokens_estimated,
            estimated_cost_usd=estimated_cost_usd,
            raw_output={"selected_chunks": [chunk.metadata for chunk in selected_chunks if chunk.metadata]},
            parsed_output={"items": []},
            status="skipped",
            message=message,
        )


def to_openai_strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    strict_schema = copy.deepcopy(schema)
    _normalize_json_schema_node(strict_schema)
    return strict_schema


def _normalize_json_schema_node(node: Any) -> None:
    if isinstance(node, list):
        for item in node:
            _normalize_json_schema_node(item)
        return
    if not isinstance(node, dict):
        return

    node.pop("default", None)
    node.pop("examples", None)

    defs = node.get("$defs")
    if isinstance(defs, dict):
        for definition in defs.values():
            _normalize_json_schema_node(definition)

    properties = node.get("properties")
    if isinstance(properties, dict):
        node["additionalProperties"] = False
        node["required"] = list(properties.keys())
        for property_schema in properties.values():
            _normalize_json_schema_node(property_schema)

    if isinstance(node.get("additionalProperties"), dict):
        _normalize_json_schema_node(node["additionalProperties"])

    for key in ("items", "anyOf", "oneOf", "allOf", "prefixItems"):
        if key in node:
            _normalize_json_schema_node(node[key])
