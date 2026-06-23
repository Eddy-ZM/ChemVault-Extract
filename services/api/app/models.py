from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import (
    BatchJobItemStatus,
    BatchJobStatus,
    BatchJobType,
    JobType,
    ReviewStatus,
    SubscriptionStatus,
    UserPlan,
    UserRole,
    WorkspaceMemberStatus,
    WorkspaceRole,
)
from app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default=UserRole.USER.value, index=True)
    plan: Mapped[str] = mapped_column(String(32), default=UserPlan.FREE.value, index=True)
    plan_override: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    monthly_ai_file_limit: Mapped[int] = mapped_column(Integer, default=10)
    monthly_ai_cost_limit_usd: Mapped[float] = mapped_column(Float, default=5.00)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    projects: Mapped[list[Project]] = relationship(back_populates="user")
    ai_settings: Mapped[UserAiSettings | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    usage_records: Mapped[list[AiUsageRecord]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[list[ApiKey]] = relationship(back_populates="user", cascade="all, delete-orphan")
    api_request_logs: Mapped[list[ApiRequestLog]] = relationship(back_populates="user", cascade="all, delete-orphan")
    webhook_endpoints: Mapped[list[WebhookEndpoint]] = relationship(back_populates="user", cascade="all, delete-orphan")
    owned_workspaces: Mapped[list[Workspace]] = relationship(
        foreign_keys="Workspace.owner_user_id",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    workspace_memberships: Mapped[list[WorkspaceMember]] = relationship(
        foreign_keys="WorkspaceMember.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    batch_jobs: Mapped[list[BatchJob]] = relationship(back_populates="user")


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255))
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    plan: Mapped[str] = mapped_column(String(64), default=UserPlan.LAB.value, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped[User] = relationship(foreign_keys=[owner_user_id], back_populates="owned_workspaces")
    members: Mapped[list[WorkspaceMember]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    projects: Mapped[list[Project]] = relationship(back_populates="workspace")
    batch_jobs: Mapped[list[BatchJob]] = relationship(back_populates="workspace")
    api_keys: Mapped[list[ApiKey]] = relationship(back_populates="workspace")
    api_request_logs: Mapped[list[ApiRequestLog]] = relationship(back_populates="workspace")
    webhook_endpoints: Mapped[list[WebhookEndpoint]] = relationship(back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_members_workspace_user"),
        UniqueConstraint("workspace_id", "invited_email", name="uq_workspace_members_workspace_invited_email"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default=WorkspaceRole.MEMBER.value, index=True)
    status: Mapped[str] = mapped_column(String(32), default=WorkspaceMemberStatus.INVITED.value, index=True)
    invited_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    invite_token: Mapped[str] = mapped_column(String(128), unique=True, default=new_id, index=True)
    invited_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="members")
    user: Mapped[User | None] = relationship(foreign_keys=[user_id], back_populates="workspace_memberships")
    invited_by: Mapped[User | None] = relationship(foreign_keys=[invited_by_user_id])


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User | None] = relationship(back_populates="projects")
    workspace: Mapped[Workspace | None] = relationship(back_populates="projects")
    documents: Mapped[list[Document]] = relationship(back_populates="project")
    export_jobs: Mapped[list[ExportJob]] = relationship(back_populates="project", cascade="all, delete-orphan")
    usage_records: Mapped[list[AiUsageRecord]] = relationship(back_populates="project", cascade="all, delete-orphan")
    batch_jobs: Mapped[list[BatchJob]] = relationship(back_populates="project")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(32), index=True)
    mime_type: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(1024), unique=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    project: Mapped[Project] = relationship(back_populates="documents")
    jobs: Mapped[list[ExtractionJob]] = relationship(back_populates="document", cascade="all, delete-orphan")
    pages: Mapped[list[DocumentPage]] = relationship(back_populates="document", cascade="all, delete-orphan")
    blocks: Mapped[list[DocumentBlock]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chemical_entities: Mapped[list[ChemicalEntity]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    reaction_records: Mapped[list[ReactionRecord]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    measurement_records: Mapped[list[MeasurementRecord]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    review_items: Mapped[list[ReviewItem]] = relationship(back_populates="document", cascade="all, delete-orphan")


class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    job_type: Mapped[str] = mapped_column(String(64), default=JobType.PARSE.value, index=True)
    status: Mapped[str] = mapped_column(String(64), index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[Document] = relationship(back_populates="jobs")
    runs: Mapped[list[ExtractionRun]] = relationship(back_populates="job", cascade="all, delete-orphan")
    usage_records: Mapped[list[AiUsageRecord]] = relationship(back_populates="extraction_job")
    batch_items: Mapped[list[BatchJobItem]] = relationship(back_populates="extraction_job")


class ExtractionRun(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("extraction_jobs.id"), index=True)
    extractor_type: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_chunk_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    selected_chunk_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    input_tokens_estimated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens_estimated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_output: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)
    parsed_output: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[ExtractionJob] = relationship(back_populates="runs")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer, index=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    width: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="pages")


class DocumentBlock(Base):
    __tablename__ = "document_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    block_type: Mapped[str] = mapped_column(String(64), index=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    html: Mapped[str | None] = mapped_column(Text, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="blocks")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, index=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="chunks")


class ChemicalEntity(Base):
    __tablename__ = "chemical_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    raw_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    name: Mapped[str] = mapped_column(String(512), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    normalized_name: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    formula: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_formula: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smiles: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    canonical_smiles: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    inchi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inchi_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cas: Mapped[str | None] = mapped_column(String(255), nullable=True)
    identifiers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pubchem_cid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    molecular_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    normalized_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_amount: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    normalized_unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    validation_status: Mapped[str] = mapped_column(String(64), default="needs_review")
    validation_warnings: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    enrichment_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enrichment_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[Document] = relationship(back_populates="chemical_entities")


class ReactionRecord(Base):
    __tablename__ = "reaction_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    reaction_name: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    raw_reactants: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    normalized_reactants: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    raw_products: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    normalized_products: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    raw_reagents: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    normalized_reagents: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    raw_solvents: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    normalized_solvents: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    raw_catalysts: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    normalized_catalysts: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    raw_temperature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_temperature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_time: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_time: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_yield_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_yield_unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    normalized_yield_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_yield_unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reactants: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    products: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    conditions: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    yield_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    validation_status: Mapped[str] = mapped_column(String(64), default="needs_review")
    validation_warnings: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[Document] = relationship(back_populates="reaction_records")


class MeasurementRecord(Base):
    __tablename__ = "measurement_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    measurement_type: Mapped[str] = mapped_column(String(128), index=True)
    normalized_measurement_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    normalized_unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_conditions: Mapped[list[dict] | dict | None] = mapped_column(JSON, nullable=True)
    normalized_conditions: Mapped[list[dict] | dict | None] = mapped_column(JSON, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(64), default="needs_review")
    validation_warnings: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    value_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[Document] = relationship(back_populates="measurement_records")


class ReviewItem(Base):
    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(128), index=True)
    record_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(64), default=ReviewStatus.PENDING.value, index=True)
    issue_type: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[Document] = relationship(back_populates="review_items")


class UserAiSettings(Base):
    __tablename__ = "user_ai_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_ai_settings_user_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64), default="openai")
    use_own_api_key: Mapped[bool] = mapped_column(Boolean, default=False)
    encrypted_openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_model: Mapped[str] = mapped_column(String(255), default="gpt-5.4")
    fallback_model: Mapped[str] = mapped_column(String(255), default="gpt-5.5")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="ai_settings")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(32), index=True)
    masked_key: Mapped[str] = mapped_column(String(64))
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="api_keys")
    workspace: Mapped[Workspace | None] = relationship(back_populates="api_keys")
    request_logs: Mapped[list[ApiRequestLog]] = relationship(back_populates="api_key")


class ApiRequestLog(Base):
    __tablename__ = "api_request_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    api_key_id: Mapped[str | None] = mapped_column(ForeignKey("api_keys.id"), nullable=True, index=True)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    method: Mapped[str] = mapped_column(String(16), index=True)
    path: Mapped[str] = mapped_column(String(1024), index=True)
    status_code: Mapped[int] = mapped_column(Integer, index=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    ip_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="api_request_logs")
    api_key: Mapped[ApiKey | None] = relationship(back_populates="request_logs")
    workspace: Mapped[Workspace | None] = relationship(back_populates="api_request_logs")


class AiUsageRecord(Base):
    __tablename__ = "ai_usage_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    batch_job_id: Mapped[str | None] = mapped_column(ForeignKey("batch_jobs.id"), nullable=True, index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    extraction_job_id: Mapped[str | None] = mapped_column(ForeignKey("extraction_jobs.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(64), default="openai", index=True)
    model: Mapped[str] = mapped_column(String(255))
    input_tokens_estimated: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens_estimated: Mapped[int] = mapped_column(Integer, default=0)
    actual_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    platform_estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    user_paid_estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    used_own_api_key: Mapped[bool] = mapped_column(Boolean, default=False)
    is_user_provided_api_key: Mapped[bool] = mapped_column(Boolean, default=False)
    actual_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="estimated", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="usage_records")
    project: Mapped[Project] = relationship(back_populates="usage_records")
    extraction_job: Mapped[ExtractionJob | None] = relationship(back_populates="usage_records")


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(64), default=BatchJobType.UPLOAD_PARSE.value, index=True)
    status: Mapped[str] = mapped_column(String(64), default=BatchJobStatus.QUEUED.value, index=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(back_populates="batch_jobs")
    workspace: Mapped[Workspace | None] = relationship(back_populates="batch_jobs")
    user: Mapped[User] = relationship(back_populates="batch_jobs")
    items: Mapped[list[BatchJobItem]] = relationship(back_populates="batch_job", cascade="all, delete-orphan")


class BatchJobItem(Base):
    __tablename__ = "batch_job_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    batch_job_id: Mapped[str] = mapped_column(ForeignKey("batch_jobs.id"), index=True)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    extraction_job_id: Mapped[str | None] = mapped_column(ForeignKey("extraction_jobs.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(64), default=BatchJobItemStatus.QUEUED.value, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    batch_job: Mapped[BatchJob] = relationship(back_populates="items")
    document: Mapped[Document | None] = relationship()
    extraction_job: Mapped[ExtractionJob | None] = relationship(back_populates="batch_items")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    plan: Mapped[str] = mapped_column(String(64), default=UserPlan.FREE.value, index=True)
    status: Mapped[str] = mapped_column(String(64), default=SubscriptionStatus.FREE.value, index=True)
    billing_interval: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latest_invoice_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    last_payment_status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    external_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    external_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="subscriptions")


class BillingEvent(Base):
    __tablename__ = "billing_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    stripe_event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(255), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    target_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(255), index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    status: Mapped[str] = mapped_column(String(64), default="queued", index=True)
    export_format: Mapped[str] = mapped_column(String(64), index=True)
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    project: Mapped[Project] = relationship(back_populates="export_jobs")


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    url: Mapped[str] = mapped_column(String(2048))
    secret_hash: Mapped[str] = mapped_column(String(128))
    encrypted_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    secret_preview: Mapped[str | None] = mapped_column(String(64), nullable=True)
    events: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="webhook_endpoints")
    workspace: Mapped[Workspace | None] = relationship(back_populates="webhook_endpoints")
    deliveries: Mapped[list[WebhookDelivery]] = relationship(back_populates="webhook_endpoint", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    webhook_endpoint_id: Mapped[str] = mapped_column(ForeignKey("webhook_endpoints.id"), index=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(255), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(64), default="queued", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    webhook_endpoint: Mapped[WebhookEndpoint] = relationship(back_populates="deliveries")
