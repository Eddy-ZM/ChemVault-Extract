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
