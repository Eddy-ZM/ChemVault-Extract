import io

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Document, DocumentBlock, DocumentChunk, DocumentPage, ExtractionJob, ExtractionRun
from app.workers.worker import process_job


def test_worker_parses_uploaded_markdown_and_saves_pages_blocks_chunks(api_client, fake_storage):
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
        runs = db.scalars(select(ExtractionRun).where(ExtractionRun.job_id == job.id).order_by(ExtractionRun.created_at)).all()

    assert document.status == "parsed"
    assert job.status == "review_ready"
    assert job.error is None
    assert [run.status for run in runs] == ["parsing", "chunking", "review_ready"]
    assert len(pages) == 1
    assert any(block.section == "Experimental" for block in blocks)
    assert any(chunk.section == "Experimental" and "Reaction at 80 C." in chunk.text for chunk in chunks)


def test_parsed_content_endpoints_return_structured_records(api_client, fake_storage):
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("table.csv", io.BytesIO(b"compound,yield\nA,75\n"), "text/csv")},
    ).json()
    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)
    document_id = upload["document"]["id"]

    pages = api_client.get(f"/documents/{document_id}/pages")
    blocks = api_client.get(f"/documents/{document_id}/blocks")
    chunks = api_client.get(f"/documents/{document_id}/chunks")

    assert pages.status_code == 200
    assert blocks.status_code == 200
    assert chunks.status_code == 200
    assert pages.json()[0]["pageNumber"] == 1
    assert blocks.json()[0]["blockType"] == "table"
    assert chunks.json()[0]["section"] == "Tables"
