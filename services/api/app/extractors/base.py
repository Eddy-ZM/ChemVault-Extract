from dataclasses import dataclass

from app.models import DocumentChunk


@dataclass(slots=True)
class ExtractionResult:
    extractor_type: str
    model_name: str
    input_chunk_ids: list[str]
    raw_output: dict | list | str | None
    parsed_output: dict | list | None
    status: str
    message: str | None = None
    error: str | None = None


class BaseStructuredExtractor:
    extractor_type = "base"
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
            raw_output=None,
            parsed_output={"items": []},
            status="skipped",
            message="No AI provider configured; extraction skipped without generating records.",
        )
