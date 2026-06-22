from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ExtractionJobRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    job_type: str = Field(serialization_alias="jobType")
    status: str
    error: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class DocumentRead(ApiModel):
    id: str
    project_id: str = Field(serialization_alias="projectId")
    filename: str
    original_filename: str = Field(serialization_alias="originalFilename")
    file_type: str = Field(serialization_alias="fileType")
    mime_type: str = Field(serialization_alias="mimeType")
    storage_key: str = Field(serialization_alias="storageKey")
    status: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class DocumentWithLatestJob(DocumentRead):
    latest_job: ExtractionJobRead | None = Field(default=None, serialization_alias="latestJob")


class UploadDocumentResponse(ApiModel):
    document: DocumentRead
    job: ExtractionJobRead


class DocumentPageRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    page_number: int = Field(serialization_alias="pageNumber")
    text: str | None = None
    image_key: str | None = Field(default=None, serialization_alias="imageKey")
    width: float | None = None
    height: float | None = None
    metadata_: dict | None = Field(default=None, serialization_alias="metadata")
    created_at: datetime = Field(serialization_alias="createdAt")


class DocumentBlockRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    page_number: int | None = Field(default=None, serialization_alias="pageNumber")
    block_type: str = Field(serialization_alias="blockType")
    section: str | None = None
    text: str | None = None
    html: str | None = None
    bbox: dict | None = None
    metadata_: dict | None = Field(default=None, serialization_alias="metadata")
    created_at: datetime = Field(serialization_alias="createdAt")


class DocumentChunkRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    chunk_index: int = Field(serialization_alias="chunkIndex")
    section: str | None = None
    page_start: int | None = Field(default=None, serialization_alias="pageStart")
    page_end: int | None = Field(default=None, serialization_alias="pageEnd")
    text: str
    token_count: int | None = Field(default=None, serialization_alias="tokenCount")
    created_at: datetime = Field(serialization_alias="createdAt")


class ChemicalEntityRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    name: str
    entity_type: str | None = Field(default=None, serialization_alias="entityType")
    normalized_name: str | None = Field(default=None, serialization_alias="normalizedName")
    identifiers: dict | None = None
    evidence: dict
    confidence: float | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ReactionRecordRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    reaction_name: str | None = Field(default=None, serialization_alias="reactionName")
    reactants: dict | None = None
    products: dict | None = None
    conditions: dict | list[dict] | None = None
    yield_text: str | None = Field(default=None, serialization_alias="yieldText")
    evidence: dict
    confidence: float | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class MeasurementRecordRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    measurement_type: str = Field(serialization_alias="measurementType")
    subject: str | None = None
    value_text: str | None = Field(default=None, serialization_alias="valueText")
    value_numeric: float | None = Field(default=None, serialization_alias="valueNumeric")
    unit: str | None = None
    conditions: dict | list[dict] | None = None
    evidence: dict
    confidence: float | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ReviewItemRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    record_type: str = Field(serialization_alias="recordType")
    record_id: str | None = Field(default=None, serialization_alias="recordId")
    status: str
    issue_type: str | None = Field(default=None, serialization_alias="issueType")
    message: str | None = None
    extracted_data: dict | None = Field(default=None, serialization_alias="extractedData")
    evidence: dict | None = None
    confidence: float | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ReviewItemUpdate(ApiModel):
    status: str | None = None
    extractedData: dict | None = None


class DocumentExtractionsRead(ApiModel):
    chemical_entities: list[ChemicalEntityRead] = Field(serialization_alias="chemicalEntities")
    reactions: list[ReactionRecordRead]
    measurements: list[MeasurementRecordRead]
    review_items: list[ReviewItemRead] = Field(serialization_alias="reviewItems")


class AICostEstimateRead(ApiModel):
    document_id: str = Field(serialization_alias="documentId")
    selected_chunks: int = Field(serialization_alias="selectedChunks")
    estimated_input_tokens: int = Field(serialization_alias="estimatedInputTokens")
    estimated_output_tokens: int = Field(serialization_alias="estimatedOutputTokens")
    model: str
    estimated_cost_usd: float = Field(serialization_alias="estimatedCostUsd")
    warning: str


class AIExtractionJobResponse(ApiModel):
    job: ExtractionJobRead
    estimated_cost: AICostEstimateRead = Field(serialization_alias="estimatedCost")
