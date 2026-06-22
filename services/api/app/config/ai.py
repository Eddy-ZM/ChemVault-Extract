from __future__ import annotations

from dataclasses import dataclass, field

from app.config import Settings
from app.models import DocumentChunk


CHUNK_SECTION_PRIORITY = (
    "Experimental",
    "Materials and Methods",
    "Methods",
    "Results",
    "Supporting Information",
    "Tables",
    "Table",
    "Abstract",
    "Introduction",
)


AI_COST_WARNING = "AI extraction may incur OpenAI API costs."

MODEL_PRICING = {
    "gpt-5.4": {
        "input_per_1m": 2.50,
        "output_per_1m": 15.00,
        "cached_input_per_1m": 0.25,
    },
}


@dataclass(slots=True)
class AISettings:
    provider: str
    default_model: str
    fallback_model: str
    max_chunks_per_document: int
    max_chunk_chars: int
    enable_fallback_model: bool
    estimated_input_token_ratio: float
    monthly_free_file_limit: int
    openai_api_key: str | None = None


@dataclass(slots=True)
class SelectedChunk:
    id: str
    section: str | None
    page_start: int | None
    page_end: int | None
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class CostEstimate:
    document_id: str
    selected_chunks: int
    selected_chunk_ids: list[str]
    estimated_input_tokens: int
    estimated_output_tokens: int
    model: str
    estimated_cost_usd: float
    warning: str = AI_COST_WARNING


def get_ai_settings(settings: Settings) -> AISettings:
    return AISettings(
        provider=settings.ai_provider,
        default_model=settings.openai_model,
        fallback_model=settings.openai_fallback_model,
        max_chunks_per_document=settings.ai_max_chunks_per_document,
        max_chunk_chars=settings.ai_max_chunk_chars,
        enable_fallback_model=settings.ai_enable_fallback_model,
        estimated_input_token_ratio=settings.ai_estimated_input_token_ratio,
        monthly_free_file_limit=settings.ai_monthly_free_file_limit,
        openai_api_key=settings.openai_api_key,
    )


def estimate_tokens(text: str, ratio: float = 0.25) -> int:
    return max(1, int(len(text) * ratio)) if text else 0


def estimate_ai_cost(*, input_tokens: int, output_tokens: int, model: str) -> dict:
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-5.4"])
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    estimated_cost = input_cost + output_cost
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "estimated_cost_usd": round(estimated_cost, 6),
        "pricing": pricing,
    }


def estimate_cost_usd(*, model: str, input_tokens: int, output_tokens: int) -> float:
    return estimate_ai_cost(input_tokens=input_tokens, output_tokens=output_tokens, model=model)["estimated_cost_usd"]


def select_chunks_for_ai(chunks: list[DocumentChunk], ai_settings: AISettings) -> list[SelectedChunk]:
    ordered = sorted(chunks, key=_chunk_priority_key)
    selected: list[SelectedChunk] = []
    for chunk in ordered:
        if _is_reference_section(chunk.section):
            continue
        text = chunk.text or ""
        used_text = text[: ai_settings.max_chunk_chars]
        metadata: dict = {}
        if len(text) > ai_settings.max_chunk_chars:
            metadata = {
                "truncated": True,
                "original_chars": len(text),
                "used_chars": len(used_text),
            }
        selected.append(
            SelectedChunk(
                id=chunk.id,
                section=chunk.section,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                text=used_text,
                metadata=metadata,
            )
        )
        if len(selected) >= ai_settings.max_chunks_per_document:
            break
    return selected


def estimate_ai_cost_for_chunks(
    *,
    document_id: str,
    chunks: list[DocumentChunk],
    ai_settings: AISettings,
    extractor_calls: int = 4,
) -> CostEstimate:
    selected = select_chunks_for_ai(chunks, ai_settings)
    selected_text = "\n\n".join(chunk.text for chunk in selected)
    input_tokens = estimate_tokens(selected_text, ai_settings.estimated_input_token_ratio) * extractor_calls
    output_tokens = int(input_tokens * 0.25)
    cost = estimate_ai_cost(input_tokens=input_tokens, output_tokens=output_tokens, model=ai_settings.default_model)
    return CostEstimate(
        document_id=document_id,
        selected_chunks=len(selected),
        selected_chunk_ids=[chunk.id for chunk in selected],
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        model=ai_settings.default_model,
        estimated_cost_usd=cost["estimated_cost_usd"],
    )


def _chunk_priority_key(chunk: DocumentChunk) -> tuple[int, int]:
    section = chunk.section or ""
    for index, preferred_section in enumerate(CHUNK_SECTION_PRIORITY):
        if preferred_section.casefold() in section.casefold():
            return (index, chunk.chunk_index)
    return (len(CHUNK_SECTION_PRIORITY), chunk.chunk_index)


def _is_reference_section(section: str | None) -> bool:
    normalized = (section or "").casefold()
    return "reference" in normalized or "bibliography" in normalized
