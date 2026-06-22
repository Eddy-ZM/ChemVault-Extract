from pathlib import Path

from app.parsers.interface import ParsedBlock, ParsedDocument, ParsedPage
from app.parsers.sections import detect_section


def _paragraphs(text: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                chunks.append(" ".join(current).strip())
                current = []
            continue
        current.append(stripped)
    if current:
        chunks.append(" ".join(current).strip())
    return chunks


def parse_text_file(file_path: str, *, markdown: bool = False) -> ParsedDocument:
    path = Path(file_path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    blocks: list[ParsedBlock] = []
    current_section: str | None = None
    current_paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal current_paragraph
        if current_paragraph:
            text = " ".join(current_paragraph).strip()
            if text:
                blocks.append(
                    ParsedBlock(
                        block_type="paragraph",
                        page_number=1,
                        section=current_section,
                        text=text,
                    )
                )
            current_paragraph = []

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue

        heading_text = stripped
        is_heading = False
        if markdown and stripped.startswith("#"):
            heading_text = stripped.lstrip("#").strip()
            is_heading = True
        elif not markdown and len(stripped) <= 80 and detect_section(stripped):
            is_heading = True

        if is_heading:
            flush_paragraph()
            current_section = detect_section(heading_text) or heading_text
            blocks.append(
                ParsedBlock(
                    block_type="heading",
                    page_number=1,
                    section=current_section,
                    text=heading_text,
                    metadata={"source": "markdown" if markdown else "text"},
                )
            )
        else:
            current_paragraph.append(stripped)

    flush_paragraph()
    page_text = "\n\n".join(block.text or "" for block in blocks if block.text)
    if not page_text:
        page_text = "\n\n".join(_paragraphs(raw))

    return ParsedDocument(
        metadata={"parser": "markdown" if markdown else "text", "filename": path.name},
        pages=[ParsedPage(page_number=1, text=page_text)],
        blocks=blocks,
    )
