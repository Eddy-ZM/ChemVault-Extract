from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.extractors.chemical_extractor import ChemicalEntityExtractor
from app.extractors.measurement_extractor import MeasurementExtractor
from app.extractors.metadata_extractor import MetadataExtractor
from app.extractors.reaction_extractor import ReactionExtractor
from app.models import DocumentChunk, ExtractionJob, ExtractionRun


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
    model_name = settings.ai_model if settings.ai_extraction_provider != "none" else "offline-no-provider"

    for extractor_class in EXTRACTORS:
        extractor = extractor_class(model_name=model_name)
        result = extractor.extract(job.document_id, chunks)
        db.add(
            ExtractionRun(
                job_id=job.id,
                extractor_type=result.extractor_type,
                model_name=result.model_name,
                input_chunk_ids=result.input_chunk_ids,
                raw_output=result.raw_output,
                parsed_output=result.parsed_output,
                status=result.status,
                message=result.message,
                error=result.error,
            )
        )
    db.commit()
