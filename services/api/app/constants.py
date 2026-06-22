from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    REVIEW_READY = "review_ready"
    FAILED = "failed"


class JobStatus(StrEnum):
    QUEUED = "queued"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    REVIEW_READY = "review_ready"
    FAILED = "failed"


ALLOWED_FILE_TYPES = {"pdf", "docx", "csv", "xlsx", "txt", "md"}
