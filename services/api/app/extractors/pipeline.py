from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.config.ai import (
    estimate_ai_cost_for_chunks,
    estimate_cost_usd,
    estimate_tokens,
    get_ai_settings,
    select_chunks_for_ai,
)
from app.constants import ExtractorType
from app.extractors.chemical_extractor import ChemicalEntityExtractor
from app.extractors.base import BaseStructuredExtractor, ExtractionResult
from app.extractors.measurement_extractor import MeasurementExtractor
from app.extractors.metadata_extractor import MetadataExtractor
from app.extractors.openai_client import OpenAIClientError, OpenAIStructuredOutputClient
from app.extractors.prompts import SYSTEM_PROMPT
from app.extractors.reaction_extractor import ReactionExtractor
from app.models import (
    ChemicalEntity,
    DocumentChunk,
    ExtractionJob,
    ExtractionRun,
    MeasurementRecord,
    ReactionRecord,
    ReviewItem,
)
from app.validators.chemistry_validator import normalize_confidence
from app.validators.evidence_validator import validate_evidence


EXTRACTORS = (
    MetadataExtractor,
    ChemicalEntityExtractor,
    ReactionExtractor,
    MeasurementExtractor,
)


def run_structured_extraction(db: Session, job: ExtractionJob, settings: Settings) -> None:
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == job.document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    ai_settings = get_ai_settings(settings)
    selected_chunks = select_chunks_for_ai(chunks, ai_settings)
    estimate = estimate_ai_cost_for_chunks(document_id=job.document_id, chunks=chunks, ai_settings=ai_settings)
    model_name = ai_settings.default_model if ai_settings.provider == "openai" else "offline-no-provider"
    per_run_input_tokens = int(estimate.estimated_input_tokens / len(EXTRACTORS)) if EXTRACTORS else 0
    per_run_output_tokens = int(estimate.estimated_output_tokens / len(EXTRACTORS)) if EXTRACTORS else 0
    per_run_cost = estimate_cost_usd(
        model=model_name,
        input_tokens=per_run_input_tokens,
        output_tokens=per_run_output_tokens,
    )

    for extractor_class in EXTRACTORS:
        extractor = extractor_class(model_name=model_name)
        if ai_settings.provider != "openai":
            result = extractor.skipped_result(
                selected_chunks=selected_chunks,
                provider=ai_settings.provider,
                input_tokens_estimated=0,
                output_tokens_estimated=0,
                estimated_cost_usd=0,
                message="No AI provider configured; extraction skipped without generating records.",
            )
            _save_run(db, job, result)
            continue

        if not ai_settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Please configure it before running AI extraction.")

        client = OpenAIStructuredOutputClient(ai_settings.openai_api_key)
        result = _run_openai_extractor(
            extractor=extractor,
            client=client,
            model_name=ai_settings.default_model,
            document_id=job.document_id,
            selected_chunks=selected_chunks,
            provider=ai_settings.provider,
            input_tokens_estimated=per_run_input_tokens,
            output_tokens_estimated=per_run_output_tokens,
            estimated_cost_usd=per_run_cost,
        )
        _save_run(db, job, result)
        if result.status == "completed":
            _persist_extraction_items(db, job, result.extractor_type, result.parsed_output or {}, chunks)
            continue
        if not ai_settings.enable_fallback_model:
            continue

        fallback_input_tokens = per_run_input_tokens
        fallback_output_tokens = per_run_output_tokens
        fallback_cost = estimate_cost_usd(
            model=ai_settings.fallback_model,
            input_tokens=fallback_input_tokens,
            output_tokens=fallback_output_tokens,
        )
        fallback_extractor = extractor_class(model_name=ai_settings.fallback_model)
        fallback_result = _run_openai_extractor(
            extractor=fallback_extractor,
            client=client,
            model_name=ai_settings.fallback_model,
            document_id=job.document_id,
            selected_chunks=selected_chunks,
            provider=ai_settings.provider,
            input_tokens_estimated=fallback_input_tokens,
            output_tokens_estimated=fallback_output_tokens,
            estimated_cost_usd=fallback_cost,
            message_prefix="fallback",
        )
        _save_run(db, job, fallback_result)
        if fallback_result.status == "completed":
            _persist_extraction_items(
                db,
                job,
                fallback_result.extractor_type,
                fallback_result.parsed_output or {},
                chunks,
            )
    db.commit()


def _run_openai_extractor(
    *,
    extractor: BaseStructuredExtractor,
    client: OpenAIStructuredOutputClient,
    model_name: str,
    document_id: str,
    selected_chunks,
    provider: str,
    input_tokens_estimated: int,
    output_tokens_estimated: int,
    estimated_cost_usd: float,
    message_prefix: str | None = None,
) -> ExtractionResult:
    selected_chunk_ids = [chunk.id for chunk in selected_chunks]
    try:
        raw_output, parsed_output = client.create_structured_output(
            model=model_name,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=extractor.build_prompt(document_id=document_id, selected_chunks=selected_chunks),
            schema_name=extractor.schema_name,
            json_schema=extractor.json_schema(),
        )
        validated_output = extractor.validate_output(parsed_output)
        return ExtractionResult(
            extractor_type=extractor.extractor_type,
            model_name=model_name,
            input_chunk_ids=selected_chunk_ids,
            selected_chunk_ids=selected_chunk_ids,
            provider=provider,
            input_tokens_estimated=input_tokens_estimated,
            output_tokens_estimated=output_tokens_estimated,
            estimated_cost_usd=estimated_cost_usd,
            raw_output=raw_output,
            parsed_output=validated_output,
            status="completed",
            message=message_prefix,
        )
    except (OpenAIClientError, ValueError) as exc:
        return ExtractionResult(
            extractor_type=extractor.extractor_type,
            model_name=model_name,
            input_chunk_ids=selected_chunk_ids,
            selected_chunk_ids=selected_chunk_ids,
            provider=provider,
            input_tokens_estimated=input_tokens_estimated,
            output_tokens_estimated=output_tokens_estimated,
            estimated_cost_usd=estimated_cost_usd,
            raw_output=None,
            parsed_output=None,
            status="failed",
            message=message_prefix,
            error=str(exc),
        )


def _save_run(db: Session, job: ExtractionJob, result: ExtractionResult) -> None:
    db.add(
        ExtractionRun(
            job_id=job.id,
            extractor_type=result.extractor_type,
            model_name=result.model_name,
            input_chunk_ids=result.input_chunk_ids,
            selected_chunk_ids=result.selected_chunk_ids,
            provider=result.provider,
            input_tokens_estimated=result.input_tokens_estimated,
            output_tokens_estimated=result.output_tokens_estimated,
            estimated_cost_usd=result.estimated_cost_usd,
            raw_output=result.raw_output,
            parsed_output=result.parsed_output,
            status=result.status,
            message=result.message,
            error=result.error,
        )
    )


def _persist_extraction_items(
    db: Session,
    job: ExtractionJob,
    extractor_type: str,
    parsed_output: dict,
    chunks: list[DocumentChunk],
) -> None:
    items = parsed_output.get("items") or []
    for item in items:
        evidence = item.get("evidence")
        evidence_result = validate_evidence(document_id=job.document_id, evidence=evidence, chunks=chunks)
        review_status = evidence_result.review_status
        confidence = normalize_confidence(item.get("confidence"))
        if extractor_type == ExtractorType.CHEMICAL_ENTITIES.value:
            record = ChemicalEntity(
                document_id=job.document_id,
                name=item["name"],
                entity_type=item.get("role"),
                identifiers={
                    "formula": item.get("formula"),
                    "smiles": item.get("smiles"),
                    "inchi": item.get("inchi"),
                    "cas": item.get("cas"),
                },
                evidence=evidence or {},
                confidence=confidence,
            )
            record_type = "chemical_entity"
        elif extractor_type == ExtractorType.REACTIONS.value:
            record = ReactionRecord(
                document_id=job.document_id,
                reaction_name=item.get("reaction_name"),
                reactants={"items": item.get("reactants", [])},
                products={"items": item.get("products", [])},
                conditions={
                    "reagents": item.get("reagents", []),
                    "solvents": item.get("solvents", []),
                    "catalysts": item.get("catalysts", []),
                    "temperature": item.get("temperature"),
                    "time": item.get("time"),
                    "atmosphere": item.get("atmosphere"),
                    "procedure": item.get("procedure"),
                },
                yield_text=_join_optional(item.get("yield_value"), item.get("yield_unit")),
                evidence=evidence or {},
                confidence=confidence,
            )
            record_type = "reaction"
        elif extractor_type == ExtractorType.MEASUREMENTS.value:
            record = MeasurementRecord(
                document_id=job.document_id,
                measurement_type=item["measurement_type"],
                subject=item.get("target"),
                value_text=item.get("value"),
                unit=item.get("unit"),
                conditions=item.get("conditions"),
                evidence=evidence or {},
                confidence=confidence,
            )
            record_type = "measurement"
        else:
            record = None
            record_type = "metadata"

        if record is not None:
            db.add(record)
            db.flush()
            record_id = record.id
        else:
            record_id = None
        db.add(
            ReviewItem(
                document_id=job.document_id,
                record_type=record_type,
                record_id=record_id,
                status=review_status,
                message="; ".join(evidence_result.errors) if evidence_result.errors else None,
                extracted_data=item,
                evidence=evidence,
                confidence=confidence,
            )
        )


def _join_optional(value: str | None, unit: str | None) -> str | None:
    if value and unit:
        return f"{value} {unit}"
    return value or unit
