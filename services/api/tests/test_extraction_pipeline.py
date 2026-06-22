import io

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    ChemicalEntity,
    DocumentChunk,
    ExtractionJob,
    ExtractionRun,
    MeasurementRecord,
    ReactionRecord,
    ReviewItem,
)
from app.workers.worker import process_job


def test_extract_ai_endpoint_creates_offline_ai_job(api_client, fake_queue):
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("paper.md", io.BytesIO(b"# Abstract\nA test paper."), "text/markdown")},
    ).json()

    response = api_client.post(f"/documents/{upload['document']['id']}/extract-ai")

    assert response.status_code == 201
    body = response.json()
    assert body["documentId"] == upload["document"]["id"]
    assert body["jobType"] == "ai_extraction"
    assert body["status"] == "queued"
    assert fake_queue.pushed[-1] == body["id"]


def test_worker_runs_offline_extraction_without_creating_fake_records(api_client, fake_storage):
    upload = api_client.post(
        "/documents/upload",
        files={
            "file": (
                "paper.md",
                io.BytesIO(
                    b"# Abstract\nA sample paper.\n\n"
                    b"## Experimental\nThe product was obtained as a white solid in 82% yield."
                ),
                "text/markdown",
            )
        },
    ).json()
    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)

    ai_job = api_client.post(f"/documents/{upload['document']['id']}/extract-ai").json()
    process_job(ai_job["id"], storage=fake_storage, step_delay_seconds=0)

    with SessionLocal() as db:
        job = db.get(ExtractionJob, ai_job["id"])
        runs = db.scalars(
            select(ExtractionRun).where(ExtractionRun.job_id == job.id).order_by(ExtractionRun.created_at)
        ).all()
        extractor_runs = [run for run in runs if run.extractor_type]
        chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == upload["document"]["id"])).all()
        chemicals = db.scalars(select(ChemicalEntity).where(ChemicalEntity.document_id == job.document_id)).all()
        reactions = db.scalars(select(ReactionRecord).where(ReactionRecord.document_id == job.document_id)).all()
        measurements = db.scalars(
            select(MeasurementRecord).where(MeasurementRecord.document_id == job.document_id)
        ).all()
        review_items = db.scalars(select(ReviewItem).where(ReviewItem.document_id == job.document_id)).all()

    assert job.status == "review_ready"
    assert chunks
    assert [run.status for run in runs if not run.extractor_type] == ["extracting", "validating", "review_ready"]
    assert {run.extractor_type for run in extractor_runs} == {
        "metadata",
        "chemical_entities",
        "reactions",
        "measurements",
    }
    assert {run.status for run in extractor_runs} == {"skipped"}
    assert all(run.model_name == "offline-no-provider" for run in extractor_runs)
    assert all(run.parsed_output == {"items": []} for run in extractor_runs)
    assert chemicals == []
    assert reactions == []
    assert measurements == []
    assert review_items == []


def test_review_items_can_be_listed_and_updated(api_client):
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("notes.txt", io.BytesIO(b"Experimental\nAspirin was measured."), "text/plain")},
    ).json()
    document_id = upload["document"]["id"]
    with SessionLocal() as db:
        item = ReviewItem(
            document_id=document_id,
            record_type="chemical_entity",
            status="needs_review",
            extracted_data={"name": "Aspirin", "role": "analyte"},
            evidence={
                "document_id": document_id,
                "chunk_id": "missing",
                "page": 1,
                "section": "Experimental",
                "quote": "",
            },
            confidence=0.4,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        review_item_id = item.id

    list_response = api_client.get(f"/documents/{document_id}/review-items")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == review_item_id
    assert list_response.json()[0]["status"] == "needs_review"
    assert list_response.json()[0]["extractedData"]["name"] == "Aspirin"

    patch_response = api_client.patch(
        f"/review-items/{review_item_id}",
        json={"status": "approved", "extractedData": {"name": "aspirin", "role": "analyte"}},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "approved"
    assert patch_response.json()["extractedData"]["name"] == "aspirin"
