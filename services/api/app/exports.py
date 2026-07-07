from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import ReviewStatus
from app.models import ChemicalEntity, ExportJob, MeasurementRecord, Project, ReactionRecord, ReviewItem
from app.schemas import ChemicalEntityRead, MeasurementRecordRead, ReactionRecordRead
from app.storage import S3Storage
from app.webhook_delivery import WebhookDeliveryQueue, enqueue_webhook_event

SUPPORTED_EXPORT_FORMATS = {"json", "csv", "xlsx"}


def run_export_job(
    db: Session,
    storage: S3Storage,
    job: ExportJob,
    *,
    webhook_queue: WebhookDeliveryQueue | None = None,
) -> ExportJob:
    export_format = _normalize_export_format(job.export_format)
    job.export_format = export_format
    job.status = "running"
    job.error = None
    db.flush()

    try:
        payload = build_project_export_payload(db, job.project_id)
        content, content_type, extension = _render_export_payload(payload, export_format)
        storage_key = f"exports/{job.project_id}/{job.id}/chemvault-export.{extension}"
        storage.upload_fileobj(storage_key, io.BytesIO(content), content_type)
        job.storage_key = storage_key
        job.status = "completed"
        db.flush()
        _enqueue_export_event(db, webhook_queue, job, "export.completed")
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error = str(exc)
        db.flush()
        _enqueue_export_event(db, webhook_queue, job, "export.failed", error=str(exc))
    return job


def build_project_export_payload(db: Session, project_id: str) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "record_scope": "approved",
        "chemical_entities": [_record_json(ChemicalEntityRead.model_validate(row)) for row in _approved_records(db, project_id, ChemicalEntity, "chemical_entity")],
        "reactions": [_record_json(ReactionRecordRead.model_validate(row)) for row in _approved_records(db, project_id, ReactionRecord, "reaction")],
        "measurements": [_record_json(MeasurementRecordRead.model_validate(row)) for row in _approved_records(db, project_id, MeasurementRecord, "measurement")],
    }


def create_download_url(storage: S3Storage, storage_key: str | None) -> str | None:
    if not storage_key:
        return None
    if hasattr(storage, "create_presigned_download_url"):
        return storage.create_presigned_download_url(storage_key)
    return storage_key


def _approved_records(db: Session, project_id: str, model, record_type: str) -> list:
    return (
        db.scalars(
            select(model)
            .join(ReviewItem, ReviewItem.record_id == model.id)
            .where(
                model.document.has(project_id=project_id),
                ReviewItem.record_type == record_type,
                ReviewItem.status == ReviewStatus.APPROVED.value,
            )
            .order_by(model.created_at.desc(), model.id.desc())
        )
        .unique()
        .all()
    )


def _render_export_payload(payload: dict[str, Any], export_format: str) -> tuple[bytes, str, str]:
    if export_format == "json":
        return (
            json.dumps(payload, indent=2, ensure_ascii=False, default=str).encode("utf-8"),
            "application/json",
            "json",
        )
    if export_format == "csv":
        return _render_csv(payload), "text/csv", "csv"
    if export_format == "xlsx":
        return _render_xlsx(payload), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
    raise ValueError(f"Unsupported export format: {export_format}")


def _render_csv(payload: dict[str, Any]) -> bytes:
    output = io.StringIO()
    fieldnames = [
        "record_type",
        "record_id",
        "document_id",
        "name",
        "normalized_name",
        "value",
        "unit",
        "validation_status",
        "confidence",
        "evidence",
        "payload",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for record_type, records in _iter_export_records(payload):
        for record in records:
            writer.writerow(_csv_row(record_type, record))
    return output.getvalue().encode("utf-8")


def _render_xlsx(payload: dict[str, Any]) -> bytes:
    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)
    for sheet_name, records in (
        ("chemicals", payload["chemical_entities"]),
        ("reactions", payload["reactions"]),
        ("measurements", payload["measurements"]),
    ):
        sheet = workbook.create_sheet(sheet_name)
        rows = [_csv_row(sheet_name.rstrip("s"), record) for record in records]
        headers = list(rows[0].keys()) if rows else ["record_type", "record_id", "document_id", "payload"]
        sheet.append(headers)
        for row in rows:
            sheet.append([row.get(header, "") for header in headers])
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _iter_export_records(payload: dict[str, Any]):
    yield "chemical_entity", payload["chemical_entities"]
    yield "reaction", payload["reactions"]
    yield "measurement", payload["measurements"]


def _csv_row(record_type: str, record: dict[str, Any]) -> dict[str, str | float | None]:
    evidence = record.get("evidence") or {}
    name = (
        record.get("rawName")
        or record.get("name")
        or record.get("reactionName")
        or record.get("measurementType")
        or record.get("subject")
    )
    normalized_name = record.get("normalizedName") or record.get("normalizedMeasurementType")
    value = record.get("normalizedValue") or record.get("rawValue") or record.get("normalizedYieldValue") or record.get("rawYieldValue")
    unit = record.get("normalizedUnit") or record.get("rawUnit") or record.get("normalizedYieldUnit") or record.get("rawYieldUnit")
    return {
        "record_type": record_type,
        "record_id": record.get("id"),
        "document_id": record.get("documentId"),
        "name": _scalar(name),
        "normalized_name": _scalar(normalized_name),
        "value": _scalar(value),
        "unit": _scalar(unit),
        "validation_status": _scalar(record.get("validationStatus")),
        "confidence": record.get("confidence"),
        "evidence": _json_cell(evidence),
        "payload": _json_cell(record),
    }


def _record_json(model) -> dict[str, Any]:
    return model.model_dump(mode="json", by_alias=True)


def _normalize_export_format(value: str) -> str:
    export_format = (value or "json").strip().lower()
    if export_format not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError(f"Unsupported export format: {export_format}")
    return export_format


def _json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _scalar(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return _json_cell(value)
    return str(value)


def _enqueue_export_event(
    db: Session,
    webhook_queue: WebhookDeliveryQueue | None,
    job: ExportJob,
    event_type: str,
    *,
    error: str | None = None,
) -> None:
    project = db.get(Project, job.project_id)
    if project is None:
        return
    enqueue_webhook_event(
        db,
        webhook_queue,
        event_type=event_type,
        user_id=project.user_id,
        workspace_id=project.workspace_id,
        project_id=project.id,
        data={
            "export_job_id": job.id,
            "status": job.status,
            "format": job.export_format,
            "storage_key": job.storage_key,
            "error": error,
        },
    )
