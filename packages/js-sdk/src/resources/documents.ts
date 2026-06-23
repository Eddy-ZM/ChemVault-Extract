import type { ChemVault } from "../client.js";

export type DocumentUploadParams = {
  projectId: string;
  file: Blob | File;
  filename?: string;
  autoParse?: boolean;
  autoExtract?: boolean;
};

export class DocumentsResource {
  constructor(private readonly client: ChemVault) {}

  upload(params: DocumentUploadParams) {
    const formData = new FormData();
    formData.set("project_id", params.projectId);
    formData.set("auto_parse", String(params.autoParse ?? true));
    formData.set("auto_extract", String(params.autoExtract ?? false));
    if (params.filename) {
      formData.set("file", params.file, params.filename);
    } else {
      formData.set("file", params.file);
    }
    return this.client.request("POST", "/v1/documents", { formData });
  }

  list(params: Record<string, unknown> = {}) {
    return this.client.request("GET", "/v1/documents", { query: params });
  }

  retrieve(documentId: string) {
    return this.client.request("GET", `/v1/documents/${documentId}`);
  }

  status(documentId: string) {
    return this.client.request("GET", `/v1/documents/${documentId}/status`);
  }

  chunks(documentId: string) {
    return this.client.request("GET", `/v1/documents/${documentId}/chunks`);
  }

  estimate(documentId: string) {
    return this.client.request("POST", `/v1/documents/${documentId}/estimate`);
  }

  extract(documentId: string, params: { mode?: string; model?: string } = {}) {
    return this.client.request("POST", `/v1/documents/${documentId}/extract`, {
      body: { mode: params.mode ?? "standard", model: params.model },
    });
  }

  records(documentId: string, options: { includeUnapproved?: boolean } = {}) {
    return this.client.request("GET", `/v1/documents/${documentId}/records`, {
      query: { include_unapproved: options.includeUnapproved ?? false },
    });
  }
}
