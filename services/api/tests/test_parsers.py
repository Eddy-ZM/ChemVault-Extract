from pathlib import Path

from app.chunking import build_chunks
from app.parsers.interface import ParsedBlock
from app.parsers.registry import parse_document
from app.parsers.sections import detect_section


def test_markdown_parser_detects_headings_as_sections(tmp_path: Path):
    path = tmp_path / "paper.md"
    path.write_text(
        "# Abstract\nA short summary.\n\n"
        "## Materials & Methods\nWe mixed sodium chloride in water.\n\n"
        "## References\n[1] A paper.",
        encoding="utf-8",
    )

    parsed = parse_document(str(path), "text/markdown")

    assert parsed.errors == []
    assert parsed.pages[0].text.startswith("Abstract")
    assert [block.section for block in parsed.blocks if block.text and "sodium chloride" in block.text] == [
        "Materials and Methods"
    ]
    assert any(block.block_type == "heading" and block.section == "Abstract" for block in parsed.blocks)


def test_txt_parser_extracts_paragraph_blocks(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("Introduction\n\nFirst paragraph.\n\nSecond paragraph.", encoding="utf-8")

    parsed = parse_document(str(path), "text/plain")

    assert parsed.pages[0].page_number == 1
    assert [block.text for block in parsed.blocks if block.block_type == "paragraph"] == [
        "First paragraph.",
        "Second paragraph.",
    ]


def test_csv_parser_creates_table_block_and_text(tmp_path: Path):
    path = tmp_path / "assay.csv"
    path.write_text("compound,yield\nAspirin,75\nCaffeine,63\n", encoding="utf-8")

    parsed = parse_document(str(path), "text/csv")

    assert parsed.tables[0].csv_text == "compound,yield\nAspirin,75\nCaffeine,63\n"
    assert parsed.blocks[0].block_type == "table"
    assert parsed.blocks[0].metadata["rows"] == 2
    assert "Aspirin" in parsed.pages[0].text


def test_section_detection_supports_common_scientific_variants():
    assert detect_section("Experimental Section") == "Experimental"
    assert detect_section("Materials & Methods") == "Materials and Methods"
    assert detect_section("SI") == "Supporting Information"
    assert detect_section("REFERENCES") == "References"


def test_chunking_groups_by_section_and_excludes_references():
    blocks = [
        ParsedBlock(block_type="paragraph", page_number=1, section="Experimental", text="alpha " * 20),
        ParsedBlock(block_type="paragraph", page_number=2, section="Experimental", text="beta " * 20),
        ParsedBlock(block_type="paragraph", page_number=3, section="References", text="[1] ref"),
        ParsedBlock(block_type="table", page_number=4, section=None, text="compound,yield\nA,75"),
    ]

    chunks = build_chunks(blocks, max_tokens=12)

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert {chunk.section for chunk in chunks} >= {"Experimental", "Tables"}
    assert "References" not in {chunk.section for chunk in chunks}
    assert all(chunk.token_count <= 12 for chunk in chunks)
    assert chunks[0].page_start == 1
