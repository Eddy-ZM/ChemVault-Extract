from pathlib import Path

from app.parsers.docx import parse_docx_file
from app.parsers.interface import ParsedDocument
from app.parsers.pdf import parse_pdf_file
from app.parsers.tables import parse_csv_file, parse_xlsx_file
from app.parsers.text import parse_text_file


def parse_document(file_path: str, mime_type: str) -> ParsedDocument:
    suffix = Path(file_path).suffix.lower()
    normalized_mime = (mime_type or "").lower()

    if suffix == ".pdf" or normalized_mime == "application/pdf":
        return parse_pdf_file(file_path)
    if suffix == ".docx" or normalized_mime.endswith("wordprocessingml.document"):
        return parse_docx_file(file_path)
    if suffix == ".csv" or normalized_mime in {"text/csv", "application/csv"}:
        return parse_csv_file(file_path)
    if suffix == ".xlsx" or normalized_mime.endswith("spreadsheetml.sheet"):
        return parse_xlsx_file(file_path)
    if suffix == ".md" or normalized_mime in {"text/markdown", "text/x-markdown"}:
        return parse_text_file(file_path, markdown=True)
    if suffix == ".txt" or normalized_mime.startswith("text/"):
        return parse_text_file(file_path)

    return ParsedDocument(errors=[f"Unsupported parser for MIME type {mime_type!r} and extension {suffix!r}"])
