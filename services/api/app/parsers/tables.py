from pathlib import Path
import csv
from html import escape

from app.parsers.interface import ParsedBlock, ParsedDocument, ParsedPage, ParsedTable


def _table_html(headers: list[str], rows: list[list[object]]) -> str:
    header_cells = "".join(f"<th>{escape(str(value))}</th>" for value in headers)
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>")
    return "<table><thead><tr>" + header_cells + "</tr></thead><tbody>" + "".join(body_rows) + "</tbody></table>"


def parse_csv_file(file_path: str) -> ParsedDocument:
    path = Path(file_path)
    try:
        import pandas as pd  # type: ignore

        df = pd.read_csv(path)
        csv_text = df.to_csv(index=False)
        html = df.to_html(index=False)
        rows_count = int(len(df))
        columns = list(df.columns)
    except Exception:
        with path.open(newline="", encoding="utf-8", errors="replace") as file:
            rows = list(csv.reader(file))
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        csv_text = path.read_text(encoding="utf-8", errors="replace")
        html = _table_html(headers, data_rows)
        rows_count = len(data_rows)
        columns = headers

    metadata = {"parser": "csv", "filename": path.name, "rows": rows_count, "columns": columns}
    table = ParsedTable(page_number=1, section=None, html=html, csv_text=csv_text, metadata=metadata)
    block = ParsedBlock(
        block_type="table",
        page_number=1,
        section=None,
        text=csv_text,
        html=html,
        metadata=metadata,
    )
    return ParsedDocument(
        metadata=metadata,
        pages=[ParsedPage(page_number=1, text=csv_text)],
        blocks=[block],
        tables=[table],
    )


def parse_xlsx_file(file_path: str) -> ParsedDocument:
    path = Path(file_path)
    try:
        import pandas as pd  # type: ignore

        sheets = pd.read_excel(path, sheet_name=None)
        sheet_items = []
        for sheet_name, df in sheets.items():
            sheet_items.append(
                (
                    sheet_name,
                    df.to_csv(index=False),
                    df.to_html(index=False),
                    int(len(df)),
                    list(df.columns),
                )
            )
    except Exception:
        from openpyxl import load_workbook

        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet_items = []
        for worksheet in workbook.worksheets:
            values = list(worksheet.values)
            headers = [str(value or "") for value in values[0]] if values else []
            rows = [[value if value is not None else "" for value in row] for row in values[1:]]
            csv_lines = []
            if headers:
                csv_lines.append(",".join(headers))
            csv_lines.extend(",".join(str(value) for value in row) for row in rows)
            csv_text = "\n".join(csv_lines) + ("\n" if csv_lines else "")
            sheet_items.append((worksheet.title, csv_text, _table_html(headers, rows), len(rows), headers))

    pages: list[ParsedPage] = []
    blocks: list[ParsedBlock] = []
    tables: list[ParsedTable] = []

    for index, (sheet_name, csv_text, html, rows_count, columns) in enumerate(sheet_items, start=1):
        metadata = {
            "parser": "xlsx",
            "filename": path.name,
            "sheetName": sheet_name,
            "rows": rows_count,
            "columns": columns,
        }
        pages.append(ParsedPage(page_number=index, text=f"Sheet: {sheet_name}\n{csv_text}"))
        blocks.append(
            ParsedBlock(
                block_type="table",
                page_number=index,
                section=None,
                text=csv_text,
                html=html,
                metadata=metadata,
            )
        )
        tables.append(ParsedTable(page_number=index, section=None, html=html, csv_text=csv_text, metadata=metadata))

    return ParsedDocument(
        metadata={"parser": "xlsx", "filename": path.name, "sheetCount": len(sheet_items)},
        pages=pages,
        blocks=blocks,
        tables=tables,
    )
