from pathlib import Path

from app.parsers.interface import ParsedBlock, ParsedDocument, ParsedPage
from app.parsers.sections import detect_section


def parse_pdf_file(file_path: str) -> ParsedDocument:
    docling_result = _try_docling(file_path)
    if docling_result is not None:
        return docling_result
    return _parse_pdf_with_pypdf(file_path)


def _try_docling(file_path: str) -> ParsedDocument | None:
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
    except Exception:
        return None

    try:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        text = result.document.export_to_markdown()
    except Exception:
        return None
    if not text.strip():
        return ParsedDocument(
            errors=["No extractable text found. OCR support will be added in a later stage."]
        )

    from app.parsers.text import parse_text_file

    temp_path = Path(file_path).with_suffix(".docling.md")
    temp_path.write_text(text, encoding="utf-8")
    parsed = parse_text_file(str(temp_path), markdown=True)
    parsed.metadata.update({"parser": "docling", "source": Path(file_path).name})
    try:
        temp_path.unlink()
    except OSError:
        pass
    return parsed


def _parse_pdf_with_pypdf(file_path: str) -> ParsedDocument:
    from pypdf import PdfReader

    path = Path(file_path)
    reader = PdfReader(file_path)
    pages: list[ParsedPage] = []
    blocks: list[ParsedBlock] = []
    current_section: str | None = None
    has_text = False

    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            has_text = True
        width = float(page.mediabox.width) if page.mediabox else None
        height = float(page.mediabox.height) if page.mediabox else None
        pages.append(
            ParsedPage(
                page_number=index,
                text=text,
                width=width,
                height=height,
                metadata={"parser": "pypdf"},
            )
        )

        def add_block(block_text: str) -> None:
            nonlocal current_section
            maybe_section = detect_section(block_text)
            if maybe_section and len(block_text) <= 100:
                current_section = maybe_section
                blocks.append(
                    ParsedBlock(block_type="heading", page_number=index, section=current_section, text=block_text)
                )
            else:
                blocks.append(
                    ParsedBlock(block_type="paragraph", page_number=index, section=current_section, text=block_text)
                )

        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        if not paragraphs:
            paragraphs = [part.strip() for part in text.splitlines() if part.strip()]
        for paragraph in paragraphs:
            lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
            if len(lines) > 1 and detect_section(lines[0]):
                add_block(lines[0])
                add_block("\n".join(lines[1:]))
            else:
                add_block(paragraph)

    if not has_text:
        return ParsedDocument(
            errors=["No extractable text found. OCR support will be added in a later stage."]
        )

    return ParsedDocument(
        metadata={"parser": "pypdf", "filename": path.name},
        pages=pages,
        blocks=blocks,
    )
