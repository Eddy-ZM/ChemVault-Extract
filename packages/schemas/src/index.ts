export type JobStatus =
  | "queued"
  | "parsing"
  | "chunking"
  | "extracting"
  | "validating"
  | "review_ready"
  | "failed";

export type DocumentStatus = "uploaded" | "parsed" | "review_ready" | "failed";

export interface ExtractionJob {
  id: string;
  documentId: string;
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
