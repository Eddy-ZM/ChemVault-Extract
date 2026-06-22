from app.models import DocumentChunk
from app.validators.evidence_validator import validate_evidence


def test_evidence_validator_accepts_quote_from_document_chunk():
    chunk = DocumentChunk(
        id="chunk-1",
        document_id="doc-1",
        chunk_index=0,
        section="Experimental",
        page_start=2,
        page_end=2,
        text="The product was obtained as a white solid in 82% yield.",
        token_count=11,
    )

    result = validate_evidence(
        document_id="doc-1",
        evidence={
            "document_id": "doc-1",
            "chunk_id": "chunk-1",
            "page": 2,
            "section": "Experimental",
            "quote": "white solid in 82% yield",
        },
        chunks=[chunk],
    )

    assert result.is_valid
    assert result.review_status == "pending"
    assert result.errors == []


def test_evidence_validator_marks_missing_or_unmatched_quote_for_review():
    chunk = DocumentChunk(
        id="chunk-1",
        document_id="doc-1",
        chunk_index=0,
        section="Experimental",
        page_start=1,
        page_end=1,
        text="The product was isolated.",
        token_count=4,
    )

    missing_quote = validate_evidence(
        document_id="doc-1",
        evidence={"document_id": "doc-1", "chunk_id": "chunk-1", "page": 1, "section": "Experimental", "quote": ""},
        chunks=[chunk],
    )
    unmatched_quote = validate_evidence(
        document_id="doc-1",
        evidence={
            "document_id": "doc-1",
            "chunk_id": "chunk-1",
            "page": 1,
            "section": "Experimental",
            "quote": "not present in source",
        },
        chunks=[chunk],
    )

    assert not missing_quote.is_valid
    assert missing_quote.review_status == "needs_review"
    assert "Evidence quote is missing." in missing_quote.errors
    assert not unmatched_quote.is_valid
    assert unmatched_quote.review_status == "needs_review"
    assert "Evidence quote was not found in the source chunk." in unmatched_quote.errors
