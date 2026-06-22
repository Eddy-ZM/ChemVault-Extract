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

    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        width = float(page.mediabox.width) if page.mediabox else None
        height = float(page.mediabox.height) if page.mediabox else None
        pages.append(ParsedPage(page_number=index, text=text, width=width, height=height))
        for paragraph in [part.strip() for part in text.split("\n\n") if part.strip()]:
            maybe_section = detect_section(paragraph)
            if maybe_section and len(paragraph) <= 100:
                current_section = maybe_section
                blocks.append(
                    ParsedBlock(block_type="heading", page_number=index, section=current_section, text=paragraph)
                )
            else:
                blocks.append(
                    ParsedBlock(block_type="paragraph", page_number=index, section=current_section, text=paragraph)
                )

    return ParsedDocument(metadata={"parser": "pypdf", "filename": path.name}, pages=pages, blocks=blocks)
