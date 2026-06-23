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
    NORMALIZING = "normalizing"
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


class ValidationStatus(StrEnum):
    VALID = "valid"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class UserPlan(StrEnum):
    FREE = "free"
    STUDENT = "student"
    RESEARCHER = "researcher"
    LAB = "lab"
    ADMIN = "admin"


class AiUsageStatus(StrEnum):
    ESTIMATED = "estimated"
    COMPLETED = "completed"
    FAILED = "failed"


class SubscriptionStatus(StrEnum):
    FREE = "free"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class BillingInterval(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class WorkspaceRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class WorkspaceMemberStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    REMOVED = "removed"


class BatchJobType(StrEnum):
    UPLOAD_PARSE = "upload_parse"
    AI_EXTRACTION = "ai_extraction"
    NORMALIZATION = "normalization"
    EXPORT = "export"


class BatchJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_FAILED = "partial_failed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchJobItemStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


ALLOWED_FILE_TYPES = {"pdf", "docx", "csv", "xlsx", "txt", "md"}
