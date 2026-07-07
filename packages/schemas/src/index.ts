export type JobStatus =
  | "queued"
  | "parsing"
  | "extracting"
  | "validating"
  | "normalizing"
  | "review_ready"
  | "failed";

export type JobType = "parse" | "ai_extraction";

export type DocumentStatus = "uploaded" | "parsed" | "review_ready" | "failed";

export interface ExtractionJob {
  id: string;
  documentId: string;
  jobType: JobType;
  status: JobStatus;
  error: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Document {
  id: string;
  projectId: string;
  filename: string;
  originalFilename: string;
  fileType: string;
  mimeType: string;
  storageKey: string;
  fileSizeBytes: number;
  status: DocumentStatus;
  createdAt: string;
  updatedAt: string;
  latestJob?: ExtractionJob | null;
}

export interface UploadDocumentResponse {
  document: Document;
  job: ExtractionJob;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  role: "user" | "admin" | string;
  plan: "free" | "student" | "researcher" | "lab" | "admin" | string;
  planOverride: string | null;
  monthlyAiFileLimit: number;
  monthlyAiCostLimitUsd: number;
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokenResponse {
  accessToken: string;
  tokenType: "bearer" | string;
  user: User;
}

export interface Project {
  id: string;
  userId: string | null;
  workspaceId: string | null;
  name: string;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentPage {
  id: string;
  documentId: string;
  pageNumber: number;
  text: string | null;
  imageKey: string | null;
  width: number | null;
  height: number | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface DocumentBlock {
  id: string;
  documentId: string;
  pageNumber: number | null;
  blockType: string;
  section: string | null;
  text: string | null;
  html: string | null;
  bbox: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface DocumentChunk {
  id: string;
  documentId: string;
  chunkIndex: number;
  section: string | null;
  pageStart: number | null;
  pageEnd: number | null;
  text: string;
  tokenCount: number | null;
  createdAt: string;
}

export interface Evidence {
  page?: number;
  section?: string;
  quote?: string;
  chunkId?: string;
  chunk_id?: string;
  [key: string]: unknown;
}

export interface ChemicalEntity {
  id: string;
  documentId: string;
  rawName: string | null;
  normalizedName: string | null;
  name?: string | null;
  formula: string | null;
  normalizedFormula: string | null;
  smiles: string | null;
  canonicalSmiles: string | null;
  inchi: string | null;
  inchiKey: string | null;
  cas: string | null;
  rawAmount: string | null;
  normalizedAmount: string | null;
  amount?: string | null;
  unit: string | null;
  normalizedUnit: string | null;
  role: string | null;
  normalizedRole: string | null;
  entityType?: string | null;
  rawRole?: string | null;
  validationStatus: string | null;
  validationWarnings: unknown[] | Record<string, unknown> | string | null;
  enrichmentStatus: string | null;
  enrichmentSource: string | null;
  pubchemCid: string | null;
  molecularWeight: number | null;
  identifiers?: Record<string, unknown> | null;
  evidence: Evidence;
  confidence: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface ReactionRecord {
  id: string;
  documentId: string;
  reactionName: string | null;
  rawReactants: Array<Record<string, unknown>> | Record<string, unknown> | null;
  normalizedReactants: Array<Record<string, unknown>> | Record<string, unknown> | null;
  rawProducts: Array<Record<string, unknown>> | Record<string, unknown> | null;
  normalizedProducts: Array<Record<string, unknown>> | Record<string, unknown> | null;
  rawReagents: Array<Record<string, unknown>> | Record<string, unknown> | null;
  normalizedReagents: Array<Record<string, unknown>> | Record<string, unknown> | null;
  rawSolvents: Array<Record<string, unknown>> | Record<string, unknown> | null;
  normalizedSolvents: Array<Record<string, unknown>> | Record<string, unknown> | null;
  rawCatalysts: Array<Record<string, unknown>> | Record<string, unknown> | null;
  normalizedCatalysts: Array<Record<string, unknown>> | Record<string, unknown> | null;
  rawTemperature: string | null;
  normalizedTemperature: string | null;
  rawTime: string | null;
  normalizedTime: string | null;
  rawYieldValue: string | null;
  rawYieldUnit: string | null;
  normalizedYieldValue: string | null;
  normalizedYieldUnit: string | null;
  conditions: Record<string, unknown> | null;
  yieldText?: string | null;
  reactionId?: string | null;
  evidence: Evidence;
  confidence: number | null;
  validationStatus: string | null;
  validationWarnings: unknown[] | Record<string, unknown> | string | null;
  createdAt: string;
  updatedAt: string;
}

export interface MeasurementRecord {
  id: string;
  documentId: string;
  measurementType: string;
  normalizedMeasurementType: string | null;
  subject: string | null;
  rawValue: string | null;
  normalizedValue: string | null;
  rawUnit: string | null;
  normalizedUnit: string | null;
  rawConditions: Record<string, unknown> | Record<string, unknown>[] | null;
  normalizedConditions: Record<string, unknown> | Record<string, unknown>[] | null;
  rawText?: string | null;
  conditions: Record<string, unknown> | Array<Record<string, unknown>> | null;
  evidence: Evidence;
  confidence: number | null;
  validationStatus: string | null;
  validationWarnings: unknown[] | Record<string, unknown> | string | null;
  createdAt: string;
  updatedAt: string;
}

export type ReviewStatus = "pending" | "needs_review" | "approved" | "rejected";
export type ReviewRecordType = "chemical_entity" | "reaction" | "measurement" | "metadata";

export interface ReviewItem {
  id: string;
  documentId: string;
  recordType: ReviewRecordType | string;
  recordId: string | null;
  status: ReviewStatus | string;
  issueType: string | null;
  message: string | null;
  extractedData: Record<string, unknown> | null;
  evidence: Evidence | null;
  confidence: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentExtractions {
  chemicalEntities: ChemicalEntity[];
  reactions: ReactionRecord[];
  measurements: MeasurementRecord[];
  reviewItems: ReviewItem[];
}

export interface NormalizedRecords {
  chemicalEntities: ChemicalEntity[];
  reactions: ReactionRecord[];
  measurements: MeasurementRecord[];
}

export interface AICostEstimate {
  documentId: string;
  selectedChunks: number;
  selectedChunkIds: string[];
  estimatedInputTokens: number;
  estimatedOutputTokens: number;
  model: string;
  estimatedCostUsd: number;
  warning: string;
}

export interface AIExtractionJobResponse {
  job: ExtractionJob;
  estimatedCost: AICostEstimate;
}

export interface BatchAIExtractionResponse {
  jobs: AIExtractionJobResponse[];
}

export type WorkspaceRole = "owner" | "admin" | "member" | "viewer";
export type WorkspaceMemberStatus = "invited" | "active" | "removed";

export interface Workspace {
  id: string;
  name: string;
  ownerUserId: string;
  plan: string;
  deletedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface WorkspaceMember {
  id: string;
  workspaceId: string;
  userId: string | null;
  role: WorkspaceRole | string;
  status: WorkspaceMemberStatus | string;
  invitedEmail: string | null;
  inviteToken: string;
  invitedByUserId: string | null;
  joinedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface WorkspaceDetail extends Workspace {
  members: WorkspaceMember[];
  projects: Project[];
}

export interface BatchJobItem {
  id: string;
  batchJobId: string;
  documentId: string | null;
  extractionJobId: string | null;
  status: string;
  error: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
}

export interface BatchJob {
  id: string;
  projectId: string;
  workspaceId: string | null;
  userId: string;
  type: "upload_parse" | "ai_extraction" | string;
  status: string;
  totalItems: number;
  completedItems: number;
  failedItems: number;
  progress: number;
  error: string | null;
  estimatedTotalCostUsd: number;
  estimatedInputTokens: number;
  estimatedOutputTokens: number;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
}

export interface BatchJobDetail extends BatchJob {
  items: BatchJobItem[];
}

export interface BatchUploadResponse {
  batchJobId: string;
  documents: number;
  jobs: ExtractionJob[];
}

export interface BatchExtractAIResponse {
  batchJobId: string;
  documents: number;
  estimatedTotalCostUsd: number;
  estimatedInputTokens: number;
  estimatedOutputTokens: number;
  batchJob: BatchJob;
}

export interface ScientificDatabaseResponse {
  chemicalEntities: ChemicalEntity[];
  reactions: ReactionRecord[];
  measurements: MeasurementRecord[];
}

export interface SearchResponse {
  documents: Array<Pick<Document, "id" | "projectId" | "filename" | "fileType" | "status">>;
  chunks: Array<{
    id: string;
    documentId: string;
    section: string | null;
    pageStart: number | null;
    pageEnd: number | null;
    text: string;
  }>;
  records: Array<{
    id: string;
    documentId: string;
    recordType: string;
    label: string;
    reviewStatus: string | null;
    validationStatus: string | null;
    confidence: number | null;
    evidence: Evidence | null;
    preview: string;
  }>;
}

export interface NormalizationRequest {
  rawData?: Record<string, unknown> | null;
}

export interface NormalizeResponse {
  status: string;
  updatedRecords: number;
  reviewItems: ReviewItem[];
}

export interface AiUsageRecord {
  id: string;
  userId: string;
  projectId: string;
  workspaceId: string | null;
  batchJobId: string | null;
  documentId: string;
  extractionJobId: string | null;
  provider: string;
  model: string;
  inputTokensEstimated: number;
  outputTokensEstimated: number;
  actualInputTokens: number | null;
  actualOutputTokens: number | null;
  estimatedCostUsd: number;
  platformEstimatedCostUsd: number;
  userPaidEstimatedCostUsd: number;
  usedOwnApiKey: boolean;
  isUserProvidedApiKey: boolean;
  actualCostUsd: number | null;
  status: "estimated" | "completed" | "failed" | string;
  createdAt: string;
}

export interface CurrentMonthUsage {
  plan: string;
  filesUsed: number;
  filesLimit: number;
  estimatedCostUsedUsd: number;
  costLimitUsd: number;
  remainingFiles: number;
  remainingCostUsd: number;
  platformEstimatedCostUsedUsd: number;
  ownKeyEstimatedCostUsedUsd: number;
  projectsUsed: number;
  projectsLimit: number;
  documentsUsed: number;
  documentsLimit: number;
  storageUsedMb: number;
  storageLimitMb: number;
  remainingStorageMb: number;
  canExport: boolean;
  canBatchExtract: boolean;
  recentRecords: AiUsageRecord[];
}

export interface UserAiSettings {
  provider: string;
  useOwnApiKey: boolean;
  hasOpenAiApiKey: boolean;
  maskedOpenAiApiKey: string | null;
  defaultModel: string;
  fallbackModel: string;
  allowUserOpenAiKeys: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ExportJob {
  id: string;
  projectId: string;
  status: string;
  exportFormat: string;
  storageKey: string | null;
  downloadUrl: string | null;
  error: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface PlanLimits {
  plan: string;
  monthlyAiFileLimit: number;
  monthlyAiCostLimitUsd: number;
  maxProjects: number;
  maxDocuments: number;
  maxStorageMb: number;
  canUseOwnApiKey: boolean;
  canExport: boolean;
  canBatchExtract: boolean;
  teamMembers: number;
}

export interface Subscription {
  id: string;
  userId: string;
  plan: string;
  status: string;
  billingInterval: string | null;
  stripeCustomerId: string | null;
  stripeSubscriptionId: string | null;
  stripePriceId: string | null;
  currentPeriodStart: string | null;
  currentPeriodEnd: string | null;
  cancelAtPeriodEnd: boolean;
  trialEnd: string | null;
  latestInvoiceId: string | null;
  lastPaymentStatus: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface BillingOverview {
  subscription: Subscription | null;
  planLimits: PlanLimits;
  usage: CurrentMonthUsage;
}

export interface CheckoutSessionResponse {
  checkoutUrl: string;
}

export interface PortalSessionResponse {
  portalUrl: string;
}

export interface ContactMessage {
  id: string;
  name: string;
  email: string;
  role: string | null;
  organization: string | null;
  message: string;
  createdAt: string;
}

export type ApiKeyScope =
  | "documents:read"
  | "documents:write"
  | "extractions:read"
  | "extractions:write"
  | "records:read"
  | "exports:read"
  | "exports:write"
  | "projects:read"
  | "projects:write";

export interface ApiKey {
  id: string;
  workspaceId: string | null;
  name: string;
  keyPrefix: string;
  maskedKey: string;
  scopes: ApiKeyScope[] | string[];
  lastUsedAt: string | null;
  expiresAt: string | null;
  revokedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ApiKeyCreateResponse extends ApiKey {
  plainKey: string;
}

export interface ApiRequestLog {
  id: string;
  apiKeyId: string | null;
  workspaceId: string | null;
  method: string;
  path: string;
  statusCode: number;
  latencyMs: number;
  ipAddress: string | null;
  userAgent: string | null;
  requestId: string;
  createdAt: string;
}

export interface DeveloperUsage {
  requestsThisMonth: number;
  apiKeysActive: number;
  extractionJobsCreatedByApi: number;
  estimatedAiCostUsd: number;
  rateLimit: {
    per_minute: number;
    per_day: number;
  };
}

export interface WebhookEndpoint {
  id: string;
  workspaceId: string | null;
  url: string;
  secretPreview: string | null;
  events: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface WebhookEndpointCreateResponse extends WebhookEndpoint {
  signingSecret: string;
}

export interface WebhookSecretRotateResponse {
  id: string;
  secretPreview: string | null;
  signingSecret: string;
}

export interface WebhookDelivery {
  id: string;
  webhookEndpointId: string;
  eventId: string;
  eventType: string;
  payload: Record<string, unknown>;
  status: "queued" | "delivering" | "delivered" | "failed" | "cancelled" | string;
  attemptCount: number;
  maxAttempts: number;
  nextAttemptAt: string | null;
  responseStatusCode: number | null;
  responseBodyPreview: string | null;
  error: string | null;
  createdAt: string;
  deliveredAt: string | null;
  updatedAt: string;
}
