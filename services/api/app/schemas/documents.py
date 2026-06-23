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
    file_size_bytes: int = Field(default=0, serialization_alias="fileSizeBytes")
    status: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class DocumentWithLatestJob(DocumentRead):
    latest_job: ExtractionJobRead | None = Field(default=None, serialization_alias="latestJob")


class UploadDocumentResponse(ApiModel):
    document: DocumentRead
    job: ExtractionJobRead


class UserRead(ApiModel):
    id: str
    email: str
    name: str | None = None
    role: str
    plan: str
    plan_override: str | None = Field(default=None, serialization_alias="planOverride")
    monthly_ai_file_limit: int = Field(serialization_alias="monthlyAiFileLimit")
    monthly_ai_cost_limit_usd: float = Field(serialization_alias="monthlyAiCostLimitUsd")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class AuthRegisterRequest(ApiModel):
    email: str
    password: str = Field(min_length=8)
    name: str | None = None
    turnstile_token: str | None = None
    turnstileToken: str | None = None
    cfTurnstileResponse: str | None = None

    @property
    def resolved_turnstile_token(self) -> str | None:
        return self.turnstile_token or self.turnstileToken or self.cfTurnstileResponse


class AuthLoginRequest(ApiModel):
    email: str
    password: str


class AuthTokenResponse(ApiModel):
    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(default="bearer", serialization_alias="tokenType")
    user: UserRead


class ProjectRead(ApiModel):
    id: str
    user_id: str | None = Field(default=None, serialization_alias="userId")
    workspace_id: str | None = Field(default=None, serialization_alias="workspaceId")
    name: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ProjectCreateRequest(ApiModel):
    name: str
    workspace_id: str | None = None
    workspaceId: str | None = None

    @property
    def resolved_workspace_id(self) -> str | None:
        return self.workspace_id or self.workspaceId


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
    raw_name: str | None = Field(default=None, serialization_alias="rawName")
    name: str
    normalized_name: str | None = Field(default=None, serialization_alias="normalizedName")
    entity_type: str | None = Field(default=None, serialization_alias="entityType")
    formula: str | None = None
    normalized_formula: str | None = Field(default=None, serialization_alias="normalizedFormula")
    smiles: str | None = None
    canonical_smiles: str | None = Field(default=None, serialization_alias="canonicalSmiles")
    inchi: str | None = None
    inchi_key: str | None = Field(default=None, serialization_alias="inchiKey")
    cas: str | None = None
    pubchem_cid: str | None = Field(default=None, serialization_alias="pubchemCid")
    molecular_weight: float | None = Field(default=None, serialization_alias="molecularWeight")
    role: str | None = None
    normalized_role: str | None = Field(default=None, serialization_alias="normalizedRole")
    amount: str | None = None
    normalized_amount: str | None = Field(default=None, serialization_alias="normalizedAmount")
    unit: str | None = None
    normalized_unit: str | None = Field(default=None, serialization_alias="normalizedUnit")
    validation_status: str | None = Field(default=None, serialization_alias="validationStatus")
    validation_warnings: list[str] | dict | None = Field(default=None, serialization_alias="validationWarnings")
    enrichment_status: str | None = Field(default=None, serialization_alias="enrichmentStatus")
    enrichment_source: str | None = Field(default=None, serialization_alias="enrichmentSource")
    evidence: dict
    confidence: float | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ReactionRecordRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    reaction_name: str | None = Field(default=None, serialization_alias="reactionName")
    raw_reactants: list[dict] | dict | None = Field(default=None, serialization_alias="rawReactants")
    normalized_reactants: list[dict] | dict | None = Field(default=None, serialization_alias="normalizedReactants")
    raw_products: list[dict] | dict | None = Field(default=None, serialization_alias="rawProducts")
    normalized_products: list[dict] | dict | None = Field(default=None, serialization_alias="normalizedProducts")
    raw_reagents: list[dict] | dict | None = Field(default=None, serialization_alias="rawReagents")
    normalized_reagents: list[dict] | dict | None = Field(default=None, serialization_alias="normalizedReagents")
    raw_solvents: list[dict] | dict | None = Field(default=None, serialization_alias="rawSolvents")
    normalized_solvents: list[dict] | dict | None = Field(default=None, serialization_alias="normalizedSolvents")
    raw_catalysts: list[dict] | dict | None = Field(default=None, serialization_alias="rawCatalysts")
    normalized_catalysts: list[dict] | dict | None = Field(default=None, serialization_alias="normalizedCatalysts")
    raw_temperature: str | None = Field(default=None, serialization_alias="rawTemperature")
    normalized_temperature: str | None = Field(default=None, serialization_alias="normalizedTemperature")
    raw_time: str | None = Field(default=None, serialization_alias="rawTime")
    normalized_time: str | None = Field(default=None, serialization_alias="normalizedTime")
    raw_yield_value: str | None = Field(default=None, serialization_alias="rawYieldValue")
    raw_yield_unit: str | None = Field(default=None, serialization_alias="rawYieldUnit")
    normalized_yield_value: str | None = Field(default=None, serialization_alias="normalizedYieldValue")
    normalized_yield_unit: str | None = Field(default=None, serialization_alias="normalizedYieldUnit")
    conditions: dict | list[dict] | None = None
    evidence: dict
    confidence: float | None = None
    validation_status: str | None = Field(default=None, serialization_alias="validationStatus")
    validation_warnings: list[str] | dict | None = Field(default=None, serialization_alias="validationWarnings")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class MeasurementRecordRead(ApiModel):
    id: str
    document_id: str = Field(serialization_alias="documentId")
    measurement_type: str = Field(serialization_alias="measurementType")
    normalized_measurement_type: str | None = Field(default=None, serialization_alias="normalizedMeasurementType")
    subject: str | None = None
    raw_value: str | None = Field(default=None, serialization_alias="rawValue")
    normalized_value: str | None = Field(default=None, serialization_alias="normalizedValue")
    raw_text: str | None = Field(default=None, serialization_alias="rawText")
    raw_unit: str | None = Field(default=None, serialization_alias="rawUnit")
    normalized_unit: str | None = Field(default=None, serialization_alias="normalizedUnit")
    raw_conditions: dict | list[dict] | None = Field(default=None, serialization_alias="rawConditions")
    normalized_conditions: dict | list[dict] | None = Field(default=None, serialization_alias="normalizedConditions")
    validation_status: str | None = Field(default=None, serialization_alias="validationStatus")
    validation_warnings: list[str] | dict | None = Field(default=None, serialization_alias="validationWarnings")
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


class NormalizedRecordsRead(ApiModel):
    chemical_entities: list[ChemicalEntityRead] = Field(serialization_alias="chemicalEntities")
    reactions: list[ReactionRecordRead]
    measurements: list[MeasurementRecordRead]


class AICostEstimateRead(ApiModel):
    document_id: str = Field(serialization_alias="documentId")
    selected_chunks: int = Field(serialization_alias="selectedChunks")
    estimated_input_tokens: int = Field(serialization_alias="estimatedInputTokens")
    estimated_output_tokens: int = Field(serialization_alias="estimatedOutputTokens")
    selected_chunk_ids: list[str] = Field(serialization_alias="selectedChunkIds")
    model: str
    estimated_cost_usd: float = Field(serialization_alias="estimatedCostUsd")
    warning: str


class AIExtractionJobResponse(ApiModel):
    job: ExtractionJobRead
    estimated_cost: AICostEstimateRead = Field(serialization_alias="estimatedCost")


class BatchAIExtractionRequest(ApiModel):
    documentIds: list[str] = Field(default_factory=list)

    @property
    def document_ids(self) -> list[str]:
        return self.documentIds


class BatchAIExtractionResponse(ApiModel):
    jobs: list[AIExtractionJobResponse]


class WorkspaceRead(ApiModel):
    id: str
    name: str
    owner_user_id: str = Field(serialization_alias="ownerUserId")
    plan: str
    deleted_at: datetime | None = Field(default=None, serialization_alias="deletedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class WorkspaceCreateRequest(ApiModel):
    name: str


class WorkspaceUpdateRequest(ApiModel):
    name: str | None = None


class WorkspaceMemberRead(ApiModel):
    id: str
    workspace_id: str = Field(serialization_alias="workspaceId")
    user_id: str | None = Field(default=None, serialization_alias="userId")
    role: str
    status: str
    invited_email: str | None = Field(default=None, serialization_alias="invitedEmail")
    invite_token: str = Field(serialization_alias="inviteToken")
    invited_by_user_id: str | None = Field(default=None, serialization_alias="invitedByUserId")
    joined_at: datetime | None = Field(default=None, serialization_alias="joinedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class WorkspaceDetailRead(WorkspaceRead):
    members: list[WorkspaceMemberRead] = Field(default_factory=list)
    projects: list[ProjectRead] = Field(default_factory=list)


class WorkspaceInviteRequest(ApiModel):
    email: str
    role: str = "member"


class WorkspaceMemberUpdateRequest(ApiModel):
    role: str


class WorkspaceInviteAcceptResponse(ApiModel):
    workspace: WorkspaceRead
    member: WorkspaceMemberRead


class BatchJobItemRead(ApiModel):
    id: str
    batch_job_id: str = Field(serialization_alias="batchJobId")
    document_id: str | None = Field(default=None, serialization_alias="documentId")
    extraction_job_id: str | None = Field(default=None, serialization_alias="extractionJobId")
    status: str
    error: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class BatchJobRead(ApiModel):
    id: str
    project_id: str = Field(serialization_alias="projectId")
    workspace_id: str | None = Field(default=None, serialization_alias="workspaceId")
    user_id: str = Field(serialization_alias="userId")
    type: str
    status: str
    total_items: int = Field(serialization_alias="totalItems")
    completed_items: int = Field(serialization_alias="completedItems")
    failed_items: int = Field(serialization_alias="failedItems")
    progress: float
    error: str | None = None
    estimated_total_cost_usd: float = Field(default=0.0, serialization_alias="estimatedTotalCostUsd")
    estimated_input_tokens: int = Field(default=0, serialization_alias="estimatedInputTokens")
    estimated_output_tokens: int = Field(default=0, serialization_alias="estimatedOutputTokens")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class BatchJobDetailRead(BatchJobRead):
    items: list[BatchJobItemRead] = Field(default_factory=list)


class BatchUploadResponse(ApiModel):
    batch_job_id: str = Field(serialization_alias="batchJobId")
    documents: int
    jobs: list[ExtractionJobRead] = Field(default_factory=list)


class BatchExtractAIRequest(ApiModel):
    projectId: str | None = None
    project_id: str | None = None
    documentIds: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    mode: str = "selected_documents"

    @property
    def resolved_project_id(self) -> str | None:
        return self.project_id or self.projectId

    @property
    def resolved_document_ids(self) -> list[str]:
        return self.document_ids or self.documentIds


class BatchExtractAIResponse(ApiModel):
    batch_job_id: str = Field(serialization_alias="batchJobId")
    documents: int
    estimated_total_cost_usd: float = Field(serialization_alias="estimatedTotalCostUsd")
    estimated_input_tokens: int = Field(serialization_alias="estimatedInputTokens")
    estimated_output_tokens: int = Field(serialization_alias="estimatedOutputTokens")
    batch_job: BatchJobRead = Field(serialization_alias="batchJob")


class NormalizationRequest(ApiModel):
    raw_data: dict | None = Field(default=None, alias="rawData")


class NormalizeResponse(ApiModel):
    status: str
    updated_records: int
    review_items: list[ReviewItemRead] = Field(default_factory=list, serialization_alias="reviewItems")


class AiUsageRecordRead(ApiModel):
    id: str
    user_id: str = Field(serialization_alias="userId")
    project_id: str = Field(serialization_alias="projectId")
    workspace_id: str | None = Field(default=None, serialization_alias="workspaceId")
    batch_job_id: str | None = Field(default=None, serialization_alias="batchJobId")
    document_id: str = Field(serialization_alias="documentId")
    extraction_job_id: str | None = Field(default=None, serialization_alias="extractionJobId")
    provider: str
    model: str
    input_tokens_estimated: int = Field(serialization_alias="inputTokensEstimated")
    output_tokens_estimated: int = Field(serialization_alias="outputTokensEstimated")
    actual_input_tokens: int | None = Field(default=None, serialization_alias="actualInputTokens")
    actual_output_tokens: int | None = Field(default=None, serialization_alias="actualOutputTokens")
    estimated_cost_usd: float = Field(serialization_alias="estimatedCostUsd")
    platform_estimated_cost_usd: float = Field(default=0.0, serialization_alias="platformEstimatedCostUsd")
    user_paid_estimated_cost_usd: float = Field(default=0.0, serialization_alias="userPaidEstimatedCostUsd")
    used_own_api_key: bool = Field(default=False, serialization_alias="usedOwnApiKey")
    is_user_provided_api_key: bool = Field(default=False, serialization_alias="isUserProvidedApiKey")
    actual_cost_usd: float | None = Field(default=None, serialization_alias="actualCostUsd")
    status: str
    created_at: datetime = Field(serialization_alias="createdAt")


class CurrentMonthUsageRead(ApiModel):
    plan: str
    files_used: int = Field(serialization_alias="filesUsed")
    files_limit: int = Field(serialization_alias="filesLimit")
    estimated_cost_used_usd: float = Field(serialization_alias="estimatedCostUsedUsd")
    cost_limit_usd: float = Field(serialization_alias="costLimitUsd")
    remaining_files: int = Field(serialization_alias="remainingFiles")
    remaining_cost_usd: float = Field(serialization_alias="remainingCostUsd")
    platform_estimated_cost_used_usd: float = Field(default=0.0, serialization_alias="platformEstimatedCostUsedUsd")
    own_key_estimated_cost_used_usd: float = Field(default=0.0, serialization_alias="ownKeyEstimatedCostUsedUsd")
    projects_used: int = Field(default=0, serialization_alias="projectsUsed")
    projects_limit: int = Field(default=0, serialization_alias="projectsLimit")
    documents_used: int = Field(default=0, serialization_alias="documentsUsed")
    documents_limit: int = Field(default=0, serialization_alias="documentsLimit")
    storage_used_mb: float = Field(default=0.0, serialization_alias="storageUsedMb")
    storage_limit_mb: int = Field(default=0, serialization_alias="storageLimitMb")
    remaining_storage_mb: float = Field(default=0.0, serialization_alias="remainingStorageMb")
    can_export: bool = Field(default=True, serialization_alias="canExport")
    can_batch_extract: bool = Field(default=False, serialization_alias="canBatchExtract")
    recent_records: list[AiUsageRecordRead] = Field(default_factory=list, serialization_alias="recentRecords")


class UserAiSettingsRead(ApiModel):
    provider: str
    use_own_api_key: bool = Field(serialization_alias="useOwnApiKey")
    has_openai_api_key: bool = Field(serialization_alias="hasOpenAiApiKey")
    masked_openai_api_key: str | None = Field(default=None, serialization_alias="maskedOpenAiApiKey")
    default_model: str = Field(serialization_alias="defaultModel")
    fallback_model: str = Field(serialization_alias="fallbackModel")
    allow_user_openai_keys: bool = Field(serialization_alias="allowUserOpenAiKeys")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class UserAiSettingsUpdate(ApiModel):
    useOwnApiKey: bool | None = None
    openaiApiKey: str | None = None
    defaultModel: str | None = None
    fallbackModel: str | None = None


class OpenAiKeyTestRequest(ApiModel):
    openaiApiKey: str | None = None


class OpenAiKeyTestResponse(ApiModel):
    ok: bool
    message: str


class ExportJobRead(ApiModel):
    id: str
    project_id: str = Field(serialization_alias="projectId")
    status: str
    export_format: str = Field(serialization_alias="exportFormat")
    storage_key: str | None = Field(default=None, serialization_alias="storageKey")
    error: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ExportJobCreateRequest(ApiModel):
    project_id: str = Field(alias="projectId")
    export_format: str = Field(default="json", alias="exportFormat")


class ContactMessageCreateRequest(ApiModel):
    name: str
    email: str
    role: str | None = None
    organization: str | None = None
    message: str


class ContactMessageRead(ApiModel):
    id: str
    name: str
    email: str
    role: str | None = None
    organization: str | None = None
    message: str
    created_at: datetime = Field(serialization_alias="createdAt")


class ApiKeyRead(ApiModel):
    id: str
    workspace_id: str | None = Field(default=None, serialization_alias="workspaceId")
    name: str
    key_prefix: str = Field(serialization_alias="keyPrefix")
    masked_key: str = Field(serialization_alias="maskedKey")
    scopes: list[str] = Field(default_factory=list)
    last_used_at: datetime | None = Field(default=None, serialization_alias="lastUsedAt")
    expires_at: datetime | None = Field(default=None, serialization_alias="expiresAt")
    revoked_at: datetime | None = Field(default=None, serialization_alias="revokedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ApiKeyCreateRequest(ApiModel):
    name: str
    workspace_id: str | None = None
    workspaceId: str | None = None
    scopes: list[str] = Field(default_factory=list)
    expiresInDays: int | None = None

    @property
    def resolved_workspace_id(self) -> str | None:
        return self.workspace_id or self.workspaceId


class ApiKeyCreateResponse(ApiKeyRead):
    plain_key: str = Field(serialization_alias="plainKey")


class ApiKeyRevokeResponse(ApiModel):
    id: str
    revoked_at: datetime = Field(serialization_alias="revokedAt")


class WebhookEndpointRead(ApiModel):
    id: str
    workspace_id: str | None = Field(default=None, serialization_alias="workspaceId")
    url: str
    secret_preview: str | None = Field(default=None, serialization_alias="secretPreview")
    events: list[str] = Field(default_factory=list)
    is_active: bool = Field(serialization_alias="isActive")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class WebhookEndpointCreateResponse(WebhookEndpointRead):
    signing_secret: str = Field(serialization_alias="signingSecret")


class WebhookEndpointCreateRequest(ApiModel):
    url: str
    workspace_id: str | None = None
    workspaceId: str | None = None
    events: list[str] = Field(default_factory=list)

    @property
    def resolved_workspace_id(self) -> str | None:
        return self.workspace_id or self.workspaceId


class WebhookEndpointUpdateRequest(ApiModel):
    url: str | None = None
    events: list[str] | None = None
    isActive: bool | None = None


class WebhookEndpointDeactivateResponse(ApiModel):
    id: str
    is_active: bool = Field(serialization_alias="isActive")


class WebhookSecretRotateResponse(ApiModel):
    id: str
    secret_preview: str | None = Field(default=None, serialization_alias="secretPreview")
    signing_secret: str = Field(serialization_alias="signingSecret")


class WebhookDeliveryRead(ApiModel):
    id: str
    webhook_endpoint_id: str = Field(serialization_alias="webhookEndpointId")
    event_id: str = Field(serialization_alias="eventId")
    event_type: str = Field(serialization_alias="eventType")
    payload: dict
    status: str
    attempt_count: int = Field(serialization_alias="attemptCount")
    max_attempts: int = Field(serialization_alias="maxAttempts")
    next_attempt_at: datetime | None = Field(default=None, serialization_alias="nextAttemptAt")
    response_status_code: int | None = Field(default=None, serialization_alias="responseStatusCode")
    response_body_preview: str | None = Field(default=None, serialization_alias="responseBodyPreview")
    error: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    delivered_at: datetime | None = Field(default=None, serialization_alias="deliveredAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ApiRequestLogRead(ApiModel):
    id: str
    api_key_id: str | None = Field(default=None, serialization_alias="apiKeyId")
    workspace_id: str | None = Field(default=None, serialization_alias="workspaceId")
    method: str
    path: str
    status_code: int = Field(serialization_alias="statusCode")
    latency_ms: int = Field(serialization_alias="latencyMs")
    ip_address: str | None = Field(default=None, serialization_alias="ipAddress")
    user_agent: str | None = Field(default=None, serialization_alias="userAgent")
    request_id: str = Field(serialization_alias="requestId")
    created_at: datetime = Field(serialization_alias="createdAt")


class DeveloperUsageRead(ApiModel):
    requests_this_month: int = Field(serialization_alias="requestsThisMonth")
    api_keys_active: int = Field(serialization_alias="apiKeysActive")
    extraction_jobs_created_by_api: int = Field(serialization_alias="extractionJobsCreatedByApi")
    estimated_ai_cost_usd: float = Field(serialization_alias="estimatedAiCostUsd")
    rate_limit: dict = Field(serialization_alias="rateLimit")


class V1DocumentCreateResponse(ApiModel):
    document_id: str = Field(serialization_alias="document_id")
    filename: str
    status: str
    parse_job_id: str = Field(serialization_alias="parse_job_id")
    extraction_job_id: str | None = Field(default=None, serialization_alias="extraction_job_id")


class V1DocumentStatusResponse(ApiModel):
    document_id: str = Field(serialization_alias="document_id")
    status: str
    latest_job: ExtractionJobRead | None = Field(default=None, serialization_alias="latest_job")


class V1EstimateResponse(ApiModel):
    document_id: str = Field(serialization_alias="document_id")
    model: str
    selected_chunks: int = Field(serialization_alias="selected_chunks")
    estimated_input_tokens: int = Field(serialization_alias="estimated_input_tokens")
    estimated_output_tokens: int = Field(serialization_alias="estimated_output_tokens")
    estimated_cost_usd: float = Field(serialization_alias="estimated_cost_usd")


class V1ExtractRequest(ApiModel):
    mode: str = "standard"
    model: str | None = None


class V1ExtractResponse(ApiModel):
    job_id: str = Field(serialization_alias="job_id")
    status: str
    estimated_cost_usd: float = Field(serialization_alias="estimated_cost_usd")


class V1RecordsResponse(ApiModel):
    document_id: str = Field(serialization_alias="document_id")
    chemical_entities: list[ChemicalEntityRead] = Field(default_factory=list, serialization_alias="chemical_entities")
    reactions: list[ReactionRecordRead] = Field(default_factory=list)
    measurements: list[MeasurementRecordRead] = Field(default_factory=list)
    review_summary: dict = Field(default_factory=dict, serialization_alias="review_summary")
    includes_unapproved: bool = Field(default=False, serialization_alias="includes_unapproved")


class PlanLimitsRead(ApiModel):
    plan: str
    monthly_ai_file_limit: int = Field(serialization_alias="monthlyAiFileLimit")
    monthly_ai_cost_limit_usd: float = Field(serialization_alias="monthlyAiCostLimitUsd")
    max_projects: int = Field(serialization_alias="maxProjects")
    max_documents: int = Field(serialization_alias="maxDocuments")
    max_storage_mb: int = Field(serialization_alias="maxStorageMb")
    can_use_own_api_key: bool = Field(serialization_alias="canUseOwnApiKey")
    can_export: bool = Field(serialization_alias="canExport")
    can_batch_extract: bool = Field(serialization_alias="canBatchExtract")
    team_members: int = Field(serialization_alias="teamMembers")


class SubscriptionRead(ApiModel):
    id: str
    user_id: str = Field(serialization_alias="userId")
    plan: str
    status: str
    billing_interval: str | None = Field(default=None, serialization_alias="billingInterval")
    stripe_customer_id: str | None = Field(default=None, serialization_alias="stripeCustomerId")
    stripe_subscription_id: str | None = Field(default=None, serialization_alias="stripeSubscriptionId")
    stripe_price_id: str | None = Field(default=None, serialization_alias="stripePriceId")
    current_period_start: datetime | None = Field(default=None, serialization_alias="currentPeriodStart")
    current_period_end: datetime | None = Field(default=None, serialization_alias="currentPeriodEnd")
    cancel_at_period_end: bool = Field(default=False, serialization_alias="cancelAtPeriodEnd")
    trial_end: datetime | None = Field(default=None, serialization_alias="trialEnd")
    latest_invoice_id: str | None = Field(default=None, serialization_alias="latestInvoiceId")
    last_payment_status: str | None = Field(default=None, serialization_alias="lastPaymentStatus")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class BillingOverviewRead(ApiModel):
    subscription: SubscriptionRead | None
    plan_limits: PlanLimitsRead = Field(serialization_alias="planLimits")
    usage: CurrentMonthUsageRead


class CheckoutSessionRequest(ApiModel):
    plan: str
    billing_interval: str = Field(alias="billing_interval", serialization_alias="billingInterval")


class CheckoutSessionResponse(ApiModel):
    checkout_url: str = Field(serialization_alias="checkoutUrl")


class PortalSessionResponse(ApiModel):
    portal_url: str = Field(serialization_alias="portalUrl")


class AdminPlanOverrideRequest(ApiModel):
    plan: str
    reason: str
