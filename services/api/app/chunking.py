from collections import defaultdict

from app.parsers.interface import ParsedBlock, ParsedChunk

EXCLUDED_SECTIONS = {"References"}


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def build_chunks(blocks: list[ParsedBlock], max_tokens: int = 900) -> list[ParsedChunk]:
    grouped: dict[str, list[ParsedBlock]] = defaultdict(list)
    order: list[str] = []

    for block in blocks:
        text = (block.text or "").strip()
        if not text:
            continue
        section = "Tables" if block.block_type == "table" else block.section or "Unsectioned"
        if section in EXCLUDED_SECTIONS:
            continue
        if section not in grouped:
            order.append(section)
        grouped[section].append(block)

    chunks: list[ParsedChunk] = []
    for section in order:
        current_parts: list[str] = []
        current_pages: list[int] = []
        current_tokens = 0

        def flush() -> None:
            nonlocal current_parts, current_pages, current_tokens
            if not current_parts:
                return
            chunks.append(
                ParsedChunk(
                    chunk_index=len(chunks),
                    section=section,
                    page_start=min(current_pages) if current_pages else None,
                    page_end=max(current_pages) if current_pages else None,
                    text="\n\n".join(current_parts),
                    token_count=current_tokens,
                )
            )
            current_parts = []
            current_pages = []
            current_tokens = 0

        for block in grouped[section]:
            text = (block.text or "").strip()
            token_count = estimate_tokens(text)
            if token_count > max_tokens:
                flush()
                words = text.split()
                for start in range(0, len(words), max_tokens):
                    part = " ".join(words[start : start + max_tokens])
                    chunks.append(
                        ParsedChunk(
                            chunk_index=len(chunks),
                            section=section,
                            page_start=block.page_number,
                            page_end=block.page_number,
                            text=part,
                            token_count=estimate_tokens(part),
                        )
                    )
                continue

            if current_parts and current_tokens + token_count > max_tokens:
                flush()
            current_parts.append(text)
            current_tokens += token_count
            if block.page_number is not None:
                current_pages.append(block.page_number)

        flush()

    return chunks
