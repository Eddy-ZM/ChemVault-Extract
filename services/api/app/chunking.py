from collections import defaultdict
import math
import re

from app.parsers.interface import ParsedBlock, ParsedChunk

EXCLUDED_SECTIONS = {"References"}
TOKEN_PIECE_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]|[A-Za-z0-9]+|[^\s]")


def estimate_tokens(text: str) -> int:
    """Return a conservative provider-independent token estimate.

    CJK characters and punctuation are counted individually. ASCII alpha-numeric
    runs use three characters per token, which intentionally leaves headroom for
    chemical formulae, identifiers, and SMILES compared with the common four
    characters-per-token prose heuristic.
    """
    total = 0
    for piece in TOKEN_PIECE_RE.findall(text):
        if piece.isascii() and piece.isalnum():
            total += max(1, math.ceil(len(piece) / 3))
        else:
            total += 1
    return total


def split_to_token_budget(text: str, max_tokens: int) -> list[str]:
    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1")
    parts: list[str] = []
    remaining = text.strip()
    while remaining:
        if estimate_tokens(remaining) <= max_tokens:
            parts.append(remaining)
            break

        low, high = 1, len(remaining)
        while low < high:
            middle = (low + high + 1) // 2
            if estimate_tokens(remaining[:middle]) <= max_tokens:
                low = middle
            else:
                high = middle - 1

        end = max(1, low)
        whitespace = max(remaining.rfind(" ", 0, end), remaining.rfind("\n", 0, end))
        if whitespace > 0:
            end = whitespace
        part = remaining[:end].strip()
        if not part:
            part = remaining[: max(1, low)]
            end = max(1, low)
        parts.append(part)
        remaining = remaining[end:].strip()
    return parts


def build_chunks(blocks: list[ParsedBlock], max_tokens: int = 900) -> list[ParsedChunk]:
    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1")
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
                for part in split_to_token_budget(text, max_tokens):
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
