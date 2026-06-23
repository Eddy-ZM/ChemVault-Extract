from dataclasses import dataclass, field

from app.models import DocumentChunk


@dataclass(slots=True)
class EvidenceValidationResult:
    is_valid: bool
    review_status: str
    errors: list[str] = field(default_factory=list)


def validate_evidence(
    *,
    document_id: str,
    evidence: dict | None,
    chunks: list[DocumentChunk],
) -> EvidenceValidationResult:
    errors: list[str] = []
    if not evidence:
        return EvidenceValidationResult(False, "needs_review", ["Evidence is missing."])

    chunk_id = evidence.get("chunk_id") or evidence.get("chunkId")
    chunk = next((candidate for candidate in chunks if candidate.id == chunk_id), None)
    if evidence.get("document_id") != document_id:
        errors.append("Evidence document_id does not match the current document.")
    if chunk is None:
        errors.append("Evidence chunk_id does not belong to the current document.")

    quote = (evidence.get("quote") or "").strip()
    if not quote:
        errors.append("Evidence quote is missing.")
    elif chunk is not None and quote not in chunk.text:
        errors.append("Evidence quote was not found in the source chunk.")

    page = evidence.get("page")
    if chunk is not None and page is not None:
        if chunk.page_start is not None and page < chunk.page_start:
            errors.append("Evidence page is before the source chunk page range.")
        if chunk.page_end is not None and page > chunk.page_end:
            errors.append("Evidence page is after the source chunk page range.")

    return EvidenceValidationResult(
        is_valid=not errors,
        review_status="pending" if not errors else "needs_review",
        errors=errors,
    )
