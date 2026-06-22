export type JobStatus =
  | "queued"
  | "parsing"
  | "chunking"
  | "extracting"
  | "validating"
  | "review_ready"
  | "failed";

export type DocumentStatus = "uploaded" | "review_ready" | "failed";

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
