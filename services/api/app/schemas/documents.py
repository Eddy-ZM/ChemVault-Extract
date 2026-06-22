from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ExtractionJobRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
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
