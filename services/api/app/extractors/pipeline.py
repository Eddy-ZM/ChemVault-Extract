from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_settings import build_ai_settings_for_job
from app.config import Settings
from app.config.ai import (
    estimate_ai_cost_for_chunks,
    estimate_cost_usd,
    select_chunks_for_ai,
)
from app.constants import ExtractorType, ReviewStatus, ValidationStatus
from app.extractors.base import BaseStructuredExtractor, ExtractionResult
from app.extractors.chemical_extractor import ChemicalEntityExtractor
from app.extractors.metadata_extractor import MetadataExtractor
from app.extractors.measurement_extractor import MeasurementExtractor
from app.extractors.openai_client import OpenAIClientError, OpenAIStructuredOutputClient
from app.extractors.prompts import SYSTEM_PROMPT
from app.extractors.reaction_extractor import ReactionExtractor
from app.models import (
    ChemicalEntity,
    Document,
    DocumentChunk,
    ExtractionJob,
    ExtractionRun,
    MeasurementRecord,
    ReactionRecord,
    ReviewItem,
)
from app.normalizers.chemical_normalizer import normalize_chemical_record
from app.normalizers.measurement_normalizer import normalize_measurement_record
from app.normalizers.reaction_normalizer import normalize_reaction_record
from app.normalizers.text_normalizer import normalize_whitespace
from app.validators.chemistry_validator import normalize_confidence
from app.validators.evidence_validator import EvidenceValidationResult, validate_evidence
from app.webhook_delivery import enqueue_webhook_event_for_document

EXTRACTORS = (
    MetadataExtractor,
    ChemicalEntityExtractor,
    ReactionExtractor,
    MeasurementExtractor,
)


def run_structured_extraction(db: Session, job: ExtractionJob, settings: Settings) -> None:
    chunks = db.scalars(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == job.document_id)
        .order_by(DocumentChunk.chunk_index)
    ).all()
    ai_settings = build_ai_settings_for_job(db, job, settings, include_api_key=True)
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
            if result.status == "failed":
                db.add(
                    ExtractionRun(
                        job_id=job.id,
                        extractor_type=result.extractor_type,
                        status="failed",
                        provider=result.provider,
                        error=result.error,
                        message="fallback disabled",
                    )
                )
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
            _persist_extraction_items(db, job, fallback_result.extractor_type, fallback_result.parsed_output or {}, chunks)



def normalize_records_for_job(
    db: Session,
    job_id: str | None,
    *,
    document_id: str | None = None,
    record_type: str | None = None,
    record_id: str | None = None,
    raw_data: dict | None = None,
) -> list[ReviewItem]:
    """Run normalization for extracted records for a job or a single record.

    Used by:
    - AI extraction worker (normalizing phase)
    - /documents/{id}/normalize endpoint
    - /records/{type}/{id}/renormalize endpoint
    """

    job: ExtractionJob | None = db.get(ExtractionJob, job_id) if job_id is not None else None
    target_document_id = job.document_id if job is not None else document_id
    if target_document_id is None:
        return []

    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == target_document_id).order_by(DocumentChunk.chunk_index)
    ).all()

    normalized_items: list[ReviewItem] = []

    if record_type:
        canonical_type = _normalize_record_type(record_type)
        if canonical_type == "chemical_entity":
            normalized_items.extend(
                _normalize_chemical_records(
                    db,
                    target_document_id,
                    chunks,
                    record_id=record_id,
                    raw_data_override=raw_data,
                )
            )
        elif canonical_type == "reaction":
            normalized_items.extend(
                _normalize_reaction_records(
                    db,
                    target_document_id,
                    chunks,
                    record_id=record_id,
                    raw_data_override=raw_data,
                )
            )
        elif canonical_type == "measurement":
            normalized_items.extend(
                _normalize_measurement_records(
                    db,
                    target_document_id,
                    chunks,
                    record_id=record_id,
                    raw_data_override=raw_data,
                )
            )
        else:
            return []
    else:
        normalized_items.extend(_normalize_chemical_records(db, target_document_id, chunks))
        normalized_items.extend(_normalize_reaction_records(db, target_document_id, chunks))
        normalized_items.extend(_normalize_measurement_records(db, target_document_id, chunks))

    db.commit()
    return normalized_items



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
        confidence = normalize_confidence(item.get("confidence"))

        if extractor_type == ExtractorType.CHEMICAL_ENTITIES.value:
            normalized = _safe_normalize(
                normalize_chemical_record,
                item,
                confidence,
                fallback_builder=_fallback_chemical_normalization,
            )
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = _derive_review_status(evidence_result, normalized.validation_status)
            record = ChemicalEntity(
                document_id=job.document_id,
                raw_name=_value_or_none(normalized.raw.get("name")),
                name=_value_or_none(normalized.normalized.get("normalizedName")) or _value_or_none(normalized.raw.get("name")) or "",
                entity_type=_value_or_none(normalized.raw.get("role")),
                normalized_name=_value_or_none(normalized.normalized.get("normalizedName")),
                formula=_value_or_none(normalized.raw.get("formula")),
                normalized_formula=_value_or_none(normalized.normalized.get("normalizedFormula")),
                smiles=_value_or_none(normalized.raw.get("smiles")),
                canonical_smiles=_value_or_none(normalized.normalized.get("canonicalSmiles")),
                inchi=_value_or_none(normalized.raw.get("inchi")),
                inchi_key=_value_or_none(normalized.normalized.get("inchiKey")) or _value_or_none(
                    normalized.raw.get("inchiKey")
                ),
                cas=_value_or_none(normalized.raw.get("cas")),
                identifiers={
                    "formula": _value_or_none(normalized.raw.get("formula")),
                    "smiles": _value_or_none(normalized.raw.get("smiles")),
                    "inchi": _value_or_none(normalized.raw.get("inchi")),
                    "cas": _value_or_none(normalized.raw.get("cas")),
                },
                pubchem_cid=_value_or_none(normalized.normalized.get("pubchemCid")),
                molecular_weight=_to_float(normalized.normalized.get("molecularWeight")),
                role=_value_or_none(normalized.normalized.get("role")),
                normalized_role=_value_or_none(normalized.normalized.get("normalizedRole")),
                amount=_value_or_none(normalized.raw.get("amount")),
                normalized_amount=_value_or_none(normalized.normalized.get("normalizedAmount")),
                unit=_value_or_none(normalized.raw.get("unit")),
                normalized_unit=_value_or_none(normalized.normalized.get("normalizedUnit")),
                validation_status=normalized.validation_status,
                validation_warnings=normalized.validation_warnings,
                enrichment_status=_value_or_none(normalized.normalized.get("enrichmentStatus")),
                enrichment_source=_value_or_none(normalized.normalized.get("enrichmentSource")),
                evidence=evidence or {},
                confidence=confidence,
            )
            record_type = "chemical_entity"
            extracted_data = _record_payload_for_review("chemical_entity", item, normalized)
        elif extractor_type == ExtractorType.REACTIONS.value:
            normalized = _safe_normalize(
                normalize_reaction_record,
                item,
                confidence,
                fallback_builder=_fallback_reaction_normalization,
            )
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = _derive_review_status(evidence_result, normalized.validation_status)
            record = ReactionRecord(
                document_id=job.document_id,
                reaction_name=_value_or_none(normalized.raw.get("reaction_name")),
                reactants=_value_or_none(normalized.raw.get("reactants"), []),
                products=_value_or_none(normalized.raw.get("products"), []),
                conditions={
                    "reagents": _value_or_none(normalized.raw.get("reagents"), []),
                    "solvents": _value_or_none(normalized.raw.get("solvents"), []),
                    "catalysts": _value_or_none(normalized.raw.get("catalysts"), []),
                    "temperature": normalized.raw.get("temperature"),
                    "time": normalized.raw.get("time"),
                    "atmosphere": normalized.raw.get("atmosphere"),
                    "procedure": normalized.raw.get("procedure"),
                },
                yield_text=_join_optional(normalized.raw.get("yield_value"), normalized.raw.get("yield_unit")),
                raw_reactants=_value_or_none(normalized.raw.get("reactants"), []),
                normalized_reactants=normalized.normalized.get("normalizedReactants"),
                raw_products=_value_or_none(normalized.raw.get("products"), []),
                normalized_products=normalized.normalized.get("normalizedProducts"),
                raw_reagents=_value_or_none(normalized.raw.get("reagents"), []),
                normalized_reagents=normalized.normalized.get("normalizedReagents"),
                raw_solvents=_value_or_none(normalized.raw.get("solvents"), []),
                normalized_solvents=normalized.normalized.get("normalizedSolvents"),
                raw_catalysts=_value_or_none(normalized.raw.get("catalysts"), []),
                normalized_catalysts=normalized.normalized.get("normalizedCatalysts"),
                raw_temperature=_value_or_none(normalized.raw.get("temperature")),
                normalized_temperature=_value_or_none(normalized.normalized.get("normalizedTemperature")),
                raw_time=_value_or_none(normalized.raw.get("time")),
                normalized_time=_value_or_none(normalized.normalized.get("normalizedTime")),
                raw_yield_value=_value_or_none(normalized.raw.get("yield_value")),
                raw_yield_unit=_value_or_none(normalized.raw.get("yield_unit")),
                normalized_yield_value=_value_to_string(normalized.normalized.get("normalizedYieldValue")),
                normalized_yield_unit=_value_or_none(normalized.normalized.get("normalizedYieldUnit")),
                evidence=evidence or {},
                confidence=confidence,
                validation_status=normalized.validation_status,
                validation_warnings=normalized.validation_warnings,
            )
            record_type = "reaction"
            extracted_data = _record_payload_for_review("reaction", item, normalized)
        elif extractor_type == ExtractorType.MEASUREMENTS.value:
            normalized = _safe_normalize(
                normalize_measurement_record,
                item,
                confidence,
                fallback_builder=_fallback_measurement_normalization,
            )
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = _derive_review_status(evidence_result, normalized.validation_status)
            record = MeasurementRecord(
                document_id=job.document_id,
                measurement_type=_value_or_none(normalized.raw.get("measurement_type")) or "other",
                normalized_measurement_type=_value_or_none(normalized.normalized.get("normalizedMeasurementType")),
                subject=_value_or_none(normalized.raw.get("target")),
                value_text=_value_or_none(normalized.raw.get("rawText"))
                or _value_or_none(normalized.raw.get("raw_text"))
                or _value_or_none(normalized.raw.get("value")),
                value_numeric=_to_float(normalized.normalized.get("normalizedValue")),
                unit=_value_or_none(normalized.raw.get("unit")),
                raw_value=_value_or_none(normalized.raw.get("value")),
                normalized_value=_value_to_string(normalized.normalized.get("normalizedValue")),
                raw_unit=_value_or_none(normalized.raw.get("unit")),
                normalized_unit=_value_or_none(normalized.normalized.get("normalizedUnit")),
                conditions=_value_or_none(normalized.raw.get("conditions"), []),
                raw_conditions=_value_or_none(normalized.raw.get("conditions"), []),
                normalized_conditions=_value_or_none(normalized.normalized.get("normalizedConditions"), []),
                evidence=evidence or {},
                confidence=confidence,
                validation_status=normalized.validation_status,
                validation_warnings=normalized.validation_warnings,
            )
            record_type = "measurement"
            extracted_data = _record_payload_for_review("measurement", item, normalized)
        else:
            continue

        db.add(record)
        db.flush()
        _upsert_review_item(
            db,
            job.document_id,
            record_type=record_type,
            record_id=record.id,
            status=review_status,
            extracted_data=extracted_data,
            evidence=evidence or {},
            confidence=confidence,
            messages=normalized.validation_warnings,
        )



def _normalize_chemical_records(
    db: Session,
    document_id: str,
    chunks: list[DocumentChunk],
    *,
    record_id: str | None = None,
    raw_data_override: dict | None = None,
) -> list[ReviewItem]:
    query = select(ChemicalEntity).where(ChemicalEntity.document_id == document_id)
    if record_id is not None:
        query = query.where(ChemicalEntity.id == record_id)

    records = db.scalars(query).all()
    results: list[ReviewItem] = []

    for record in records:
        raw_item = _normalize_chemical_record_payload(record, raw_data_override)
        confidence = normalize_confidence(raw_item.pop("confidence", None))
        evidence = _coerce_evidence(record.evidence)
        evidence_result = validate_evidence(document_id=document_id, evidence=evidence, chunks=chunks)
        try:
            normalized = _safe_normalize(
                normalize_chemical_record,
                raw_item,
                confidence,
                fallback_builder=_fallback_chemical_normalization,
            )
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = _derive_review_status(evidence_result, normalized.validation_status)
            record.raw_name = _value_or_none(normalized.raw.get("name"))
            record.name = (
                _value_or_none(normalized.normalized.get("normalizedName"))
                or _value_or_none(record.name)
                or _value_or_none(record.raw_name)
            )
            record.formula = _value_or_none(normalized.raw.get("formula"))
            record.normalized_formula = _value_or_none(normalized.normalized.get("normalizedFormula"))
            record.smiles = _value_or_none(normalized.raw.get("smiles"))
            record.canonical_smiles = _value_or_none(normalized.normalized.get("canonicalSmiles"))
            record.inchi = _value_or_none(normalized.raw.get("inchi"))
            record.inchi_key = _value_or_none(normalized.raw.get("inchiKey"))
            record.cas = _value_or_none(normalized.raw.get("cas"))
            record.identifiers = {
                "formula": _value_or_none(normalized.raw.get("formula")),
                "smiles": _value_or_none(normalized.raw.get("smiles")),
                "inchi": _value_or_none(normalized.raw.get("inchi")),
                "cas": _value_or_none(normalized.raw.get("cas")),
            }
            record.pubchem_cid = _value_or_none(normalized.normalized.get("pubchemCid"))
            record.molecular_weight = _to_float(normalized.normalized.get("molecularWeight"))
            record.role = _value_or_none(normalized.raw.get("role"))
            record.normalized_role = _value_or_none(normalized.normalized.get("normalizedRole"))
            record.amount = _value_or_none(normalized.raw.get("amount"))
            record.normalized_amount = _value_or_none(normalized.normalized.get("normalizedAmount"))
            record.unit = _value_or_none(normalized.raw.get("unit"))
            record.normalized_unit = _value_or_none(normalized.normalized.get("normalizedUnit"))
            record.validation_status = normalized.validation_status
            record.validation_warnings = normalized.validation_warnings
            record.enrichment_status = _value_or_none(normalized.normalized.get("enrichmentStatus"))
            record.enrichment_source = _value_or_none(normalized.normalized.get("enrichmentSource"))
            record.evidence = evidence or {}
            record.confidence = confidence
        except Exception as exc:  # noqa: BLE001
            normalized = _fallback_chemical_normalization(item=raw_item, confidence=confidence, error=str(exc))
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = "needs_review"
            record.name = _value_or_none(record.raw_name) or "Unnamed"
            record.validation_status = normalized.validation_status
            record.validation_warnings = normalized.validation_warnings
            record.evidence = evidence or {}
            record.confidence = confidence

        results.append(
            _upsert_review_item(
                db,
                document_id,
                record_type="chemical_entity",
                record_id=record.id,
                status=review_status,
                extracted_data=_record_payload_for_review(
                    "chemical_entity", {**raw_item, "evidence": evidence}, normalized
                ),
                evidence=evidence,
                confidence=confidence,
                messages=normalized.validation_warnings,
            )
        )

    return results



def _normalize_reaction_records(
    db: Session,
    document_id: str,
    chunks: list[DocumentChunk],
    *,
    record_id: str | None = None,
    raw_data_override: dict | None = None,
) -> list[ReviewItem]:
    query = select(ReactionRecord).where(ReactionRecord.document_id == document_id)
    if record_id is not None:
        query = query.where(ReactionRecord.id == record_id)

    records = db.scalars(query).all()
    results: list[ReviewItem] = []

    for record in records:
        raw_item = _normalize_reaction_record_payload(record, raw_data_override)
        confidence = normalize_confidence(raw_item.pop("confidence", None))
        evidence = _coerce_evidence(record.evidence)
        evidence_result = validate_evidence(document_id=document_id, evidence=evidence, chunks=chunks)
        try:
            normalized = _safe_normalize(
                normalize_reaction_record,
                raw_item,
                confidence,
                fallback_builder=_fallback_reaction_normalization,
            )
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = _derive_review_status(evidence_result, normalized.validation_status)
            record.reaction_name = _value_or_none(normalized.raw.get("reaction_name"))
            record.reactants = _value_or_none(normalized.raw.get("reactants"), [])
            record.products = _value_or_none(normalized.raw.get("products"), [])
            record.conditions = {
                "reagents": _value_or_none(normalized.raw.get("reagents"), []),
                "solvents": _value_or_none(normalized.raw.get("solvents"), []),
                "catalysts": _value_or_none(normalized.raw.get("catalysts"), []),
                "temperature": normalized.raw.get("temperature"),
                "time": normalized.raw.get("time"),
                "atmosphere": normalized.raw.get("atmosphere"),
                "procedure": normalized.raw.get("procedure"),
            }
            record.yield_text = _join_optional(normalized.raw.get("yield_value"), normalized.raw.get("yield_unit"))
            record.raw_reactants = _value_or_none(normalized.raw.get("reactants"), [])
            record.normalized_reactants = normalized.normalized.get("normalizedReactants")
            record.raw_products = _value_or_none(normalized.raw.get("products"), [])
            record.normalized_products = normalized.normalized.get("normalizedProducts")
            record.raw_reagents = _value_or_none(normalized.raw.get("reagents"), [])
            record.normalized_reagents = normalized.normalized.get("normalizedReagents")
            record.raw_solvents = _value_or_none(normalized.raw.get("solvents"), [])
            record.normalized_solvents = normalized.normalized.get("normalizedSolvents")
            record.raw_catalysts = _value_or_none(normalized.raw.get("catalysts"), [])
            record.normalized_catalysts = normalized.normalized.get("normalizedCatalysts")
            record.raw_temperature = _value_or_none(normalized.raw.get("temperature"))
            record.normalized_temperature = _value_or_none(normalized.normalized.get("normalizedTemperature"))
            record.raw_time = _value_or_none(normalized.raw.get("time"))
            record.normalized_time = _value_or_none(normalized.normalized.get("normalizedTime"))
            record.raw_yield_value = _value_or_none(normalized.raw.get("yield_value"))
            record.raw_yield_unit = _value_or_none(normalized.raw.get("yield_unit"))
            record.normalized_yield_value = _value_to_string(normalized.normalized.get("normalizedYieldValue"))
            record.normalized_yield_unit = _value_or_none(normalized.normalized.get("normalizedYieldUnit"))
            record.evidence = evidence or {}
            record.confidence = confidence
            record.validation_status = normalized.validation_status
            record.validation_warnings = normalized.validation_warnings
        except Exception as exc:  # noqa: BLE001
            normalized = _fallback_reaction_normalization(item=raw_item, confidence=confidence, error=str(exc))
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = "needs_review"
            record.reaction_name = _value_or_none(record.reaction_name)
            record.evidence = evidence or {}
            record.validation_status = normalized.validation_status
            record.validation_warnings = normalized.validation_warnings

        results.append(
            _upsert_review_item(
                db,
                document_id,
                record_type="reaction",
                record_id=record.id,
                status=review_status,
                extracted_data=_record_payload_for_review("reaction", {**raw_item, "evidence": evidence}, normalized),
                evidence=evidence,
                confidence=confidence,
                messages=normalized.validation_warnings or [],
            )
        )

    return results



def _normalize_measurement_records(
    db: Session,
    document_id: str,
    chunks: list[DocumentChunk],
    *,
    record_id: str | None = None,
    raw_data_override: dict | None = None,
) -> list[ReviewItem]:
    query = select(MeasurementRecord).where(MeasurementRecord.document_id == document_id)
    if record_id is not None:
        query = query.where(MeasurementRecord.id == record_id)

    records = db.scalars(query).all()
    results: list[ReviewItem] = []

    for record in records:
        raw_item = _normalize_measurement_record_payload(record, raw_data_override)
        confidence = normalize_confidence(raw_item.pop("confidence", None))
        evidence = _coerce_evidence(record.evidence)
        evidence_result = validate_evidence(document_id=document_id, evidence=evidence, chunks=chunks)
        try:
            normalized = _safe_normalize(
                normalize_measurement_record,
                raw_item,
                confidence,
                fallback_builder=_fallback_measurement_normalization,
            )
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = _derive_review_status(evidence_result, normalized.validation_status)
            record.measurement_type = _value_or_none(normalized.raw.get("measurement_type")) or "other"
            record.normalized_measurement_type = _value_or_none(normalized.normalized.get("normalizedMeasurementType"))
            record.subject = _value_or_none(normalized.raw.get("target"))
            record.value_text = (
                _value_or_none(normalized.raw.get("rawText"))
                or _value_or_none(normalized.raw.get("raw_text"))
                or _value_or_none(normalized.raw.get("value"))
            )
            record.value_numeric = _to_float(normalized.normalized.get("normalizedValue"))
            record.unit = _value_or_none(normalized.raw.get("unit"))
            record.raw_value = _value_or_none(normalized.raw.get("value"))
            record.normalized_value = _value_to_string(normalized.normalized.get("normalizedValue"))
            record.raw_unit = _value_or_none(normalized.raw.get("unit"))
            record.normalized_unit = _value_or_none(normalized.normalized.get("normalizedUnit"))
            record.conditions = _value_or_none(normalized.raw.get("conditions"), [])
            record.raw_conditions = _value_or_none(normalized.raw.get("conditions"), [])
            record.normalized_conditions = _value_or_none(normalized.normalized.get("normalizedConditions"), [])
            record.evidence = evidence or {}
            record.confidence = confidence
            record.validation_status = normalized.validation_status
            record.validation_warnings = normalized.validation_warnings
        except Exception as exc:  # noqa: BLE001
            normalized = _fallback_measurement_normalization(item=raw_item, confidence=confidence, error=str(exc))
            normalized = _merge_validation_result(normalized, evidence_result)
            review_status = "needs_review"
            record.measurement_type = _value_or_none(record.measurement_type)
            record.validation_status = normalized.validation_status
            record.validation_warnings = normalized.validation_warnings

        results.append(
            _upsert_review_item(
                db,
                document_id,
                record_type="measurement",
                record_id=record.id,
                status=review_status,
                extracted_data=_record_payload_for_review(
                    "measurement",
                    {**raw_item, "evidence": evidence},
                    normalized,
                ),
                evidence=evidence,
                confidence=confidence,
                messages=normalized.validation_warnings,
            )
        )

    return results



def _upsert_review_item(
    db: Session,
    document_id: str,
    *,
    record_type: str,
    record_id: str,
    status: str,
    extracted_data: dict,
    evidence: dict | None,
    confidence: float | None,
    messages: list[str],
) -> ReviewItem:
    existing = db.scalars(
        select(ReviewItem)
        .where(
            ReviewItem.document_id == document_id,
            ReviewItem.record_type == record_type,
            ReviewItem.record_id == record_id,
        )
        .order_by(ReviewItem.created_at.desc(), ReviewItem.id.desc())
    ).first()

    message = "; ".join(messages) if messages else None

    if existing is None:
        item = ReviewItem(
            document_id=document_id,
            record_type=record_type,
            record_id=record_id,
            status=status,
            issue_type="normalization",
            message=message,
            extracted_data=extracted_data,
            evidence=evidence,
            confidence=confidence,
        )
        db.add(item)
        db.flush()
        document = db.get(Document, document_id)
        if document is not None:
            enqueue_webhook_event_for_document(
                db,
                None,
                document=document,
                event_type="review.item_created",
                data={
                    "review_item_id": item.id,
                    "record_type": record_type,
                    "record_id": record_id,
                    "status": status,
                    "review_url": f"/documents/{document_id}/review",
                },
            )
        return item

    existing.status = status
    existing.issue_type = "normalization"
    existing.message = message
    existing.extracted_data = extracted_data
    existing.evidence = evidence
    existing.confidence = confidence
    return existing



def _merge_validation_result(
    result: NormalizationResult,
    evidence_result: EvidenceValidationResult,
) -> NormalizationResult:
    warnings: list[str] = list(result.validation_warnings or [])
    if evidence_result.errors:
        warnings.extend(evidence_result.errors)

    if not evidence_result.is_valid and result.validation_status != ValidationStatus.INVALID.value:
        result.validation_status = ValidationStatus.INVALID.value

    result.validation_warnings = warnings
    result.normalized["validationStatus"] = result.validation_status
    result.normalized["validationWarnings"] = warnings
    return result



def _safe_normalize(
    normalizer: Callable[[dict, Any], Any],
    item: dict,
    confidence: float | None,
    *,
    fallback_builder,
) -> Any | None:
    try:
        return normalizer(item=item, confidence=confidence)
    except Exception as exc:  # noqa: BLE001
        return fallback_builder(item=item, confidence=confidence, error=str(exc))


def _fallback_chemical_normalization(
    *,
    item: dict,
    confidence: float | None,
    error: str,
) -> NormalizationResult:
    warning = [f"Normalization failed: {error}"]
    normalized_name = normalize_whitespace(item.get("name")) if item.get("name") else None
    validation_status = ValidationStatus.NEEDS_REVIEW
    if confidence is not None and confidence < 0.75:
        warning.append("Confidence is below 0.75.")

    normalized = {
        "rawName": normalize_whitespace(item.get("name")),
        "normalizedName": normalized_name,
        "formula": normalize_whitespace(item.get("formula")),
        "normalizedFormula": normalize_whitespace(item.get("formula")),
        "smiles": normalize_whitespace(item.get("smiles")),
        "canonicalSmiles": normalize_whitespace(item.get("smiles")),
        "inchi": normalize_whitespace(item.get("inchi")),
        "inchiKey": normalize_whitespace(item.get("inchiKey") or item.get("inchi_key")),
        "cas": normalize_whitespace(item.get("cas")),
        "role": normalize_whitespace(item.get("role")),
        "normalizedRole": normalize_whitespace(item.get("role")),
        "amount": normalize_whitespace(item.get("amount")),
        "normalizedAmount": normalize_whitespace(item.get("amount")),
        "unit": normalize_whitespace(item.get("unit")),
        "normalizedUnit": normalize_whitespace(item.get("unit")),
        "validationStatus": validation_status.value,
        "validationWarnings": warning,
        "enrichmentStatus": None,
        "enrichmentSource": None,
    }
    if normalized_name is None:
        validation_status = ValidationStatus.INVALID
        warning.append("Name is required.")
        normalized["validationStatus"] = validation_status.value

    return NormalizationResult(
        raw={
            "name": normalize_whitespace(item.get("name")),
            "formula": normalize_whitespace(item.get("formula")),
            "smiles": normalize_whitespace(item.get("smiles")),
            "inchi": normalize_whitespace(item.get("inchi")),
            "inchiKey": normalize_whitespace(item.get("inchiKey") or item.get("inchi_key")),
            "cas": normalize_whitespace(item.get("cas")),
            "role": normalize_whitespace(item.get("role")),
            "amount": normalize_whitespace(item.get("amount")),
            "unit": normalize_whitespace(item.get("unit")),
            "evidence": item.get("evidence"),
            "confidence": confidence,
        },
        normalized=normalized,
        validation_status=validation_status.value,
        validation_warnings=warning,
    )


def _fallback_reaction_normalization(
    *,
    item: dict,
    confidence: float | None,
    error: str,
) -> NormalizationResult:
    warning = [f"Normalization failed: {error}"]
    normalized_status = ValidationStatus.NEEDS_REVIEW
    if not item.get("reactants") and not item.get("products"):
        warning.append("Missing reactants and products.")
        normalized_status = ValidationStatus.INVALID

    raw = {
        "reaction_name": normalize_whitespace(item.get("reaction_name")),
        "reactants": item.get("reactants") or [],
        "products": item.get("products") or [],
        "reagents": item.get("reagents") or [],
        "solvents": item.get("solvents") or [],
        "catalysts": item.get("catalysts") or [],
        "temperature": normalize_whitespace(item.get("temperature")),
        "time": normalize_whitespace(item.get("time")),
        "yield_value": normalize_whitespace(item.get("yield_value")),
        "yield_unit": normalize_whitespace(item.get("yield_unit")),
        "procedure": normalize_whitespace(item.get("procedure")),
        "atmosphere": normalize_whitespace(item.get("atmosphere")),
        "confidence": confidence,
        "evidence": item.get("evidence"),
    }
    normalized = {
        "reactionName": raw.get("reaction_name"),
        "rawReactants": raw.get("reactants"),
        "normalizedReactants": _fallback_chemical_list(raw.get("reactants") or []),
        "rawProducts": raw.get("products"),
        "normalizedProducts": _fallback_chemical_list(raw.get("products") or []),
        "rawReagents": raw.get("reagents"),
        "normalizedReagents": _fallback_chemical_list(raw.get("reagents") or []),
        "rawSolvents": raw.get("solvents"),
        "normalizedSolvents": _fallback_chemical_list(raw.get("solvents") or []),
        "rawCatalysts": raw.get("catalysts"),
        "normalizedCatalysts": _fallback_chemical_list(raw.get("catalysts") or []),
        "rawTemperature": raw.get("temperature"),
        "normalizedTemperature": raw.get("temperature"),
        "rawTime": raw.get("time"),
        "normalizedTime": raw.get("time"),
        "rawYieldValue": raw.get("yield_value"),
        "normalizedYieldValue": raw.get("yield_value"),
        "rawYieldUnit": raw.get("yield_unit"),
        "normalizedYieldUnit": raw.get("yield_unit"),
        "procedure": raw.get("procedure"),
        "atmosphere": raw.get("atmosphere"),
        "validationStatus": normalized_status.value,
        "validationWarnings": warning,
    }
    if confidence is not None and confidence < 0.75:
        warning.append("Confidence is below 0.75.")
    return NormalizationResult(
        raw=raw,
        normalized=normalized,
        validation_status=normalized_status.value,
        validation_warnings=warning,
    )


def _fallback_measurement_normalization(
    *,
    item: dict,
    confidence: float | None,
    error: str,
) -> NormalizationResult:
    warning = [f"Normalization failed: {error}"]
    normalized_status = ValidationStatus.NEEDS_REVIEW.value
    raw = {
        "target": normalize_whitespace(item.get("target")),
        "measurement_type": normalize_whitespace(item.get("measurement_type")),
        "value": normalize_whitespace(item.get("value")),
        "unit": normalize_whitespace(item.get("unit")),
        "conditions": item.get("conditions"),
        "raw_text": normalize_whitespace(item.get("raw_text")),
        "confidence": confidence,
        "evidence": item.get("evidence"),
    }
    if not raw.get("measurement_type"):
        warning.append("Missing measurement_type.")
        normalized_status = ValidationStatus.INVALID.value
    if raw.get("value") is None:
        warning.append("Missing measurement value.")
        normalized_status = ValidationStatus.INVALID.value
    if confidence is not None and confidence < 0.75:
        warning.append("Confidence is below 0.75.")

    normalized = {
        "measurementType": raw.get("measurement_type"),
        "normalizedMeasurementType": raw.get("measurement_type"),
        "rawValue": raw.get("value"),
        "normalizedValue": raw.get("value"),
        "rawUnit": raw.get("unit"),
        "normalizedUnit": raw.get("unit"),
        "rawConditions": raw.get("conditions"),
        "normalizedConditions": raw.get("conditions"),
        "target": raw.get("target"),
        "rawText": raw.get("raw_text"),
        "validationStatus": normalized_status,
        "validationWarnings": warning,
    }
    return NormalizationResult(
        raw=raw,
        normalized=normalized,
        validation_status=normalized_status,
        validation_warnings=warning,
    )


def _fallback_chemical_list(items: Any) -> list[dict]:
    output: list[dict] = []
    for value in items or []:
        if isinstance(value, dict):
            output.append(value)
        else:
            output.append({"name": str(value)})
    return output



def _derive_review_status(evidence_result, validation_status: str) -> str:
    if not evidence_result.is_valid:
        return ReviewStatus.NEEDS_REVIEW.value
    if validation_status == ValidationStatus.INVALID.value:
        return ReviewStatus.NEEDS_REVIEW.value
    if validation_status == ValidationStatus.NEEDS_REVIEW.value:
        return ReviewStatus.NEEDS_REVIEW.value
    return ReviewStatus.PENDING.value



def _record_payload_for_review(record_type: str, item: dict, normalized) -> dict:
    return {
        "recordType": record_type,
        "raw": normalized.raw,
        "normalized": normalized.normalized,
        "validationStatus": normalized.validation_status,
        "validationWarnings": normalized.validation_warnings,
        "sourceEvidence": item.get("evidence"),
        "originalItem": item,
    }



def _normalize_chemical_record_payload(
    record: ChemicalEntity,
    raw_data_override: dict | None,
) -> dict:
    payload = {
        "name": record.raw_name,
        "formula": record.formula,
        "smiles": record.smiles,
        "inchi": record.inchi,
        "inchiKey": record.inchi_key,
        "cas": record.cas,
        "role": record.entity_type,
        "amount": record.amount,
        "unit": record.unit,
        "confidence": record.confidence,
        "evidence": _coerce_evidence(record.evidence),
    }
    payload.update(_coerce_raw_payload(raw_data_override))
    return payload



def _normalize_reaction_record_payload(record: ReactionRecord, raw_data_override: dict | None) -> dict:
    payload = {
        "reaction_name": record.reaction_name,
        "reactants": _coerce_raw_items(record.raw_reactants),
        "products": _coerce_raw_items(record.raw_products),
        "reagents": _coerce_raw_items(record.raw_reagents),
        "solvents": _coerce_raw_items(record.raw_solvents),
        "catalysts": _coerce_raw_items(record.raw_catalysts),
        "temperature": record.raw_temperature,
        "time": record.raw_time,
        "yield_value": record.raw_yield_value,
        "yield_unit": record.raw_yield_unit,
        "procedure": record.conditions.get("procedure") if isinstance(record.conditions, dict) else None,
        "atmosphere": record.conditions.get("atmosphere") if isinstance(record.conditions, dict) else None,
        "confidence": record.confidence,
        "evidence": _coerce_evidence(record.evidence),
    }
    payload.update(_coerce_raw_payload(raw_data_override))
    return payload



def _normalize_measurement_record_payload(record: MeasurementRecord, raw_data_override: dict | None) -> dict:
    payload = {
        "measurement_type": record.measurement_type,
        "target": record.subject,
        "value": record.raw_value,
        "unit": record.raw_unit,
        "conditions": record.raw_conditions,
        "raw_text": record.value_text,
        "confidence": record.confidence,
        "evidence": _coerce_evidence(record.evidence),
    }
    payload.update(_coerce_raw_payload(raw_data_override))
    return payload



def _coerce_raw_payload(value: dict | None) -> dict:
    if not value:
        return {}
    if isinstance(value, dict) and "raw" in value and isinstance(value["raw"], dict):
        return {**value["raw"], "confidence": value.get("confidence", value.get("raw", {}).get("confidence"))}
    return value



def _coerce_raw_items(value: Any) -> list:
    if isinstance(value, dict):
        nested = value.get("items")
        if isinstance(nested, list):
            return nested
        return []
    if isinstance(value, list):
        return value
    return []



def _coerce_evidence(value: Any) -> dict | None:
    if isinstance(value, dict):
        return value
    return None



def _normalize_record_type(raw: str | None) -> str | None:
    if raw is None:
        return None

    normalized = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"chemical", "chemicalentity", "chemical_entities", "chemical_entity", "chemical-entity"}:
        return "chemical_entity"
    if normalized in {"reaction", "reaction_record", "reaction_records", "reactionrecord"}:
        return "reaction"
    if normalized in {"measurement", "measurement_record", "measurement_records", "measurementrecord"}:
        return "measurement"
    return None



def _value_or_none(value, default=None):
    return value if value is not None else default



def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None



def _value_to_string(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)



def _join_optional(value: str | None, unit: str | None) -> str | None:
    if value and unit:
        return f"{value} {unit}"
    return value or unit
