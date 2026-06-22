from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    REVIEW_READY = "review_ready"
    FAILED = "failed"


class JobStatus(StrEnum):
    QUEUED = "queued"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    REVIEW_READY = "review_ready"
    FAILED = "failed"


class JobType(StrEnum):
    PARSE = "parse"
    AI_EXTRACTION = "ai_extraction"


class ExtractorType(StrEnum):
    METADATA = "metadata"
    CHEMICAL_ENTITIES = "chemical_entities"
    REACTIONS = "reactions"
    MEASUREMENTS = "measurements"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"


ALLOWED_FILE_TYPES = {"pdf", "docx", "csv", "xlsx", "txt", "md"}
