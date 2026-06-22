export type JobStatus =
  | "queued"
  | "parsing"
  | "extracting"
  | "validating"
  | "review_ready"
  | "failed";

export type DocumentStatus = "uploaded" | "parsed" | "review_ready" | "failed";

export interface ExtractionJob {
  id: string;
  documentId: string;
  jobType: "parse" | "ai_extraction";
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
  status: DocumentStatus;
  createdAt: string;
  updatedAt: string;
  latestJob?: ExtractionJob | null;
}

export interface UploadDocumentResponse {
  document: Document;
  job: ExtractionJob;
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
  [key: string]: unknown;
}

export interface ChemicalEntity {
  id: string;
  documentId: string;
  name: string;
  entityType: string | null;
  normalizedName: string | null;
  identifiers: Record<string, unknown> | null;
  evidence: Evidence;
  confidence: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface ReactionRecord {
  id: string;
  documentId: string;
  reactionName: string | null;
  reactants: Record<string, unknown> | null;
  products: Record<string, unknown> | null;
  conditions: Record<string, unknown> | null;
  yieldText: string | null;
  evidence: Evidence;
  confidence: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface MeasurementRecord {
  id: string;
  documentId: string;
  measurementType: string;
  subject: string | null;
  valueText: string | null;
  valueNumeric: number | null;
  unit: string | null;
  conditions: Record<string, unknown> | null;
  evidence: Evidence;
  confidence: number | null;
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
