import io

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.extractors.openai_client import DeepSeekStructuredOutputClient, OpenAIStructuredOutputClient
from app.models import (
    AiUsageRecord,
    ChemicalEntity,
    Document,
    DocumentChunk,
    ExtractionJob,
    ExtractionRun,
    MeasurementRecord,
    ReactionRecord,
    ReviewItem,
)
from app.workers.worker import process_job


def test_extract_ai_endpoint_requires_openai_api_key(api_client):
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("paper.md", io.BytesIO(b"# Abstract\nA test paper."), "text/markdown")},
    ).json()

    response = api_client.post(f"/documents/{upload['document']['id']}/extract-ai")

    assert response.status_code == 400
    assert response.json()["detail"] == "Platform OpenAI API key is missing."


def test_extract_ai_endpoint_accepts_unparsed_document(api_client, fake_storage, fake_queue, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("paper.md", io.BytesIO(b"# Abstract\nA test paper."), "text/markdown")},
    ).json()

    response = api_client.post(f"/documents/{upload['document']['id']}/extract-ai")

    assert response.status_code == 201
    body = response.json()
    assert body["job"]["status"] == "queued"
    assert body["estimatedCost"]["selectedChunks"] == 0
    assert body["estimatedCost"]["estimatedCostUsd"] == 0.0
    assert body["estimatedCost"]["warning"].startswith("AI extraction may incur AI provider API costs.")
    assert fake_queue.pushed[-1] == body["job"]["id"]


def test_extract_ai_endpoint_accepts_openai_api_key(api_client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("paper.md", io.BytesIO(b"# Abstract\nA test paper."), "text/markdown")},
    ).json()
    response = api_client.post(f"/documents/{upload['document']['id']}/extract-ai")

    assert response.status_code == 201
def test_extract_ai_endpoint_creates_openai_job_when_key_is_configured(
    api_client,
    fake_queue,
    fake_storage,
    monkeypatch,
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    upload = api_client.post(
        "/documents/upload",
        files={
            "file": (
                "paper.md",
                io.BytesIO(b"# Abstract\nA test paper."), "text/markdown"),
        },
    ).json()
    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)

    response = api_client.post(f"/documents/{upload['document']['id']}/extract-ai")

    assert response.status_code == 201
    body = response.json()
    assert body["job"]["documentId"] == upload["document"]["id"]
    assert body["job"]["jobType"] == "ai_extraction"
    assert body["job"]["status"] == "queued"
    assert body["estimatedCost"]["model"] == "gpt-5.4"
    assert body["estimatedCost"]["warning"] == "AI extraction may incur AI provider API costs."
    assert fake_queue.pushed[-1] == body["job"]["id"]


def test_estimate_ai_cost_returns_selected_chunks_and_model(api_client, fake_storage):
    upload = api_client.post(
        "/documents/upload",
        files={
            "file": (
                "paper.md",
                io.BytesIO(
                    b"# Abstract\nShort summary.\n\n"
                    b"## Experimental\nThe product was obtained in 82% yield.\n\n"
                    b"## References\n[1] Reference text."
                ),
                "text/markdown",
            )
        },
    ).json()
    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)

    response = api_client.post(f"/documents/{upload['document']['id']}/estimate-ai-cost")

    assert response.status_code == 200
    body = response.json()
    assert body["documentId"] == upload["document"]["id"]
    assert body["selectedChunks"] >= 1
    assert body["selectedChunks"] <= 20
    assert body["estimatedInputTokens"] > 0
    assert body["estimatedOutputTokens"] > 0
    assert body["model"] == "gpt-5.4"
    assert body["estimatedCostUsd"] > 0
    assert body["warning"] == "AI extraction may incur AI provider API costs."


def test_extract_ai_endpoint_enforces_monthly_limit(api_client, fake_storage, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MONTHLY_FREE_FILE_LIMIT", "1")
    get_settings.cache_clear()
    upload = api_client.post(
        "/documents/upload",
        files={"file": ("paper.md", io.BytesIO(b"# Abstract\nA test paper."), "text/markdown")},
    ).json()
    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)
    with SessionLocal() as db:
        document = db.get(Document, upload["document"]["id"])
        user = document.project.user
        user.monthly_ai_file_limit = 1
        user.monthly_ai_cost_limit_usd = 5.0
        db.add(
            AiUsageRecord(
                user_id=user.id,
                project_id=document.project_id,
                document_id=upload["document"]["id"],
                provider="openai",
                model="gpt-5.4",
                input_tokens_estimated=10,
                output_tokens_estimated=10,
                estimated_cost_usd=0.01,
                status="completed",
            )
        )
        db.commit()

    response = api_client.post(f"/documents/{upload['document']['id']}/extract-ai")

    assert response.status_code == 400
    assert response.json()["detail"] == "Monthly AI extraction file limit reached."


def test_worker_runs_offline_extraction_without_creating_fake_records(api_client, fake_storage, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
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

    ai_job = api_client.post(f"/documents/{upload['document']['id']}/extract-ai").json()["job"]
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
    assert [run.status for run in runs if not run.extractor_type] == [
        "extracting",
        "validating",
        "normalizing",
        "review_ready",
    ]
    assert {run.extractor_type for run in extractor_runs} == {
        "metadata",
        "chemical_entities",
        "reactions",
        "measurements",
    }
    assert {run.status for run in extractor_runs} == {"skipped"}
    assert all(run.model_name == "offline-no-provider" for run in extractor_runs)
    assert all(run.parsed_output == {"items": []} for run in extractor_runs)
    assert all(run.provider == "none" for run in extractor_runs)
    assert all(run.estimated_cost_usd == 0 for run in extractor_runs)
    assert chemicals == []
    assert reactions == []
    assert measurements == []
    assert review_items == []


def test_worker_openai_mode_records_cost_fields_without_sending_full_document(
    api_client,
    fake_storage,
    monkeypatch,
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()

    def fake_structured_output(self, **kwargs):
        assert "Selected chunks:" in kwargs["user_prompt"]
        assert "References" not in kwargs["user_prompt"]
        return {"id": "resp_test"}, {"items": []}

    monkeypatch.setattr(OpenAIStructuredOutputClient, "create_structured_output", fake_structured_output)
    upload = api_client.post(
        "/documents/upload",
        files={
            "file": (
                "paper.md",
                io.BytesIO(
                    b"# Abstract\nA sample paper.\n\n"
                    b"## Experimental\nThe product was obtained as a white solid in 82% yield.\n\n"
                    b"## References\n[1] This reference should not be selected."
                ),
                "text/markdown",
            )
        },
    ).json()
    process_job(upload["job"]["id"], storage=fake_storage, step_delay_seconds=0)
    ai_job = api_client.post(f"/documents/{upload['document']['id']}/extract-ai").json()["job"]

    process_job(ai_job["id"], storage=fake_storage, step_delay_seconds=0)

    with SessionLocal() as db:
        runs = db.scalars(
            select(ExtractionRun).where(ExtractionRun.job_id == ai_job["id"]).order_by(ExtractionRun.created_at)
        ).all()
        extractor_runs = [run for run in runs if run.extractor_type]

    assert {run.status for run in extractor_runs} == {"completed"}
    assert all(run.provider == "openai" for run in extractor_runs)
    assert all(run.model_name == "gpt-5.4" for run in extractor_runs)
    assert all(run.input_tokens_estimated > 0 for run in extractor_runs)
    assert all(run.output_tokens_estimated > 0 for run in extractor_runs)
    assert all(run.estimated_cost_usd > 0 for run in extractor_runs)
    assert all(run.selected_chunk_ids for run in extractor_runs)


def test_worker_deepseek_mode_uses_configured_provider(
    api_client,
    fake_storage,
    monkeypatch,
):
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    get_settings.cache_clear()

    def fake_structured_output(self, **kwargs):
        assert kwargs["model"] == "deepseek-v4-flash"
        assert "Selected chunks:" in kwargs["user_prompt"]
        return {"id": "deepseek_test"}, {"items": []}

    monkeypatch.setattr(DeepSeekStructuredOutputClient, "create_structured_output", fake_structured_output)
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
    ai_job = api_client.post(f"/documents/{upload['document']['id']}/extract-ai").json()["job"]

    process_job(ai_job["id"], storage=fake_storage, step_delay_seconds=0)

    with SessionLocal() as db:
        runs = db.scalars(
            select(ExtractionRun).where(ExtractionRun.job_id == ai_job["id"]).order_by(ExtractionRun.created_at)
        ).all()
        extractor_runs = [run for run in runs if run.extractor_type]

    assert {run.status for run in extractor_runs} == {"completed"}
    assert all(run.provider == "deepseek" for run in extractor_runs)
    assert all(run.model_name == "deepseek-v4-flash" for run in extractor_runs)


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
