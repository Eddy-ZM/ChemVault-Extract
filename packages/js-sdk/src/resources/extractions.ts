import type { ChemVault } from "../client.js";

export class ExtractionsResource {
  constructor(private readonly client: ChemVault) {}

  estimate(documentId: string) {
    return this.client.request("POST", `/v1/documents/${documentId}/estimate`);
  }

  extract(documentId: string, params: { mode?: string; model?: string } = {}) {
    return this.client.request("POST", `/v1/documents/${documentId}/extract`, {
      body: { mode: params.mode ?? "standard", model: params.model },
    });
  }

  job(jobId: string) {
    return this.client.request("GET", `/v1/jobs/${jobId}`);
  }
}
