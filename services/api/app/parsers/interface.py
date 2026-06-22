from dataclasses import dataclass, field


@dataclass(slots=True)
class ParsedPage:
    page_number: int
    text: str | None = None
    width: float | None = None
    height: float | None = None


@dataclass(slots=True)
class ParsedBlock:
    block_type: str
    page_number: int | None = None
    section: str | None = None
    text: str | None = None
    html: str | None = None
    bbox: dict | None = None
    metadata: dict | None = None


@dataclass(slots=True)
class ParsedTable:
    page_number: int | None = None
    section: str | None = None
    html: str | None = None
    csv_text: str | None = None
    metadata: dict | None = None


@dataclass(slots=True)
class ParsedDocument:
    metadata: dict = field(default_factory=dict)
    pages: list[ParsedPage] = field(default_factory=list)
    blocks: list[ParsedBlock] = field(default_factory=list)
    tables: list[ParsedTable] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedChunk:
    chunk_index: int
    section: str | None
    page_start: int | None
    page_end: int | None
    text: str
    token_count: int | None
