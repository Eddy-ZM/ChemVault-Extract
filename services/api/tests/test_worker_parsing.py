import io

from sqlalchemy import select

from app.constants import JobStatus
from app.database import SessionLocal
from app.models import Document, DocumentBlock, DocumentChunk, DocumentPage, ExtractionJob, ExtractionRun
from app.workers.worker import process_job


def test_worker_parses_markdown_into_pages_blocks_and_chunks(api_client, fake_storage):
    upload = api_client.post(
        "/documents/upload",
        files={
            "file": (
                "experiment.md",
                io.BytesIO(b"# Abstract\nSummary.\n\n## Experimental Section\nReaction at 80 C."),
                "text/markdown",
            )
        },
    ).json()

    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)

    with SessionLocal() as db:
        document = db.get(Document, upload["document"]["id"])
        job = db.get(ExtractionJob, upload["job"]["id"])
        pages = db.scalars(select(DocumentPage).where(DocumentPage.document_id == document.id)).all()
        blocks = db.scalars(select(DocumentBlock).where(DocumentBlock.document_id == document.id)).all()
        chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).all()
        runs = db.scalars(
            select(ExtractionRun).where(ExtractionRun.job_id == job.id).order_by(ExtractionRun.created_at)
        ).all()

    assert document.status == "review_ready"
    assert job.status == "review_ready"
    assert job.error is None
    assert [run.status for run in runs] == ["parsing", "review_ready"]
    assert len(pages) == 1
    assert any(block.block_type == "heading" and block.section == "Abstract" for block in blocks)
    assert any(block.block_type == "paragraph" and block.section == "Experimental" for block in blocks)
    assert {chunk.section for chunk in chunks} >= {"Abstract", "Experimental"}


def test_worker_marks_scanned_pdf_without_text_as_failed(api_client, fake_storage):
    from pypdf import PdfWriter

    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(buffer)
    buffer.seek(0)

    upload = api_client.post(
        "/documents/upload",
        files={"file": ("scan.pdf", buffer, "application/pdf")},
    ).json()

    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)

    with SessionLocal() as db:
        document = db.get(Document, upload["document"]["id"])
        job = db.get(ExtractionJob, upload["job"]["id"])

    assert document.status == "failed"
    assert job.status == JobStatus.FAILED.value
    assert job.error == "No extractable text found. OCR support will be added in a later stage."


def test_parsed_content_endpoints_return_records_after_worker_parses_csv(api_client, fake_storage):
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("table.csv", io.BytesIO(b"compound,yield\nA,75\n"), "text/csv")},
    ).json()
    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)
    document_id = upload["document"]["id"]

    pages = api_client.get(f"/documents/{document_id}/pages")
    blocks = api_client.get(f"/documents/{document_id}/blocks")
    chunks = api_client.get(f"/documents/{document_id}/chunks")
    tables = api_client.get(f"/documents/{document_id}/tables")

    assert pages.status_code == 200
    assert blocks.status_code == 200
    assert chunks.status_code == 200
    assert tables.status_code == 200
    assert len(pages.json()) == 1
    assert pages.json()[0]["pageNumber"] == 1
    assert blocks.json()[0]["blockType"] == "table"
    assert blocks.json()[0]["metadata"]["rows"] == [{"compound": "A", "yield": 75}]
    assert len(chunks.json()) == 1
    assert chunks.json()[0]["section"] == "Tables"
    assert tables.json()[0]["blockType"] == "table"
