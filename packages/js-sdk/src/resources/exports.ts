import type { ChemVault } from "../client.js";

export type ExportCreateParams = {
  projectId: string;
  exportFormat?: "json" | "csv" | "xlsx" | string;
  includeUnapproved?: boolean;
};

export class ExportsResource {
  constructor(private readonly client: ChemVault) {}

  create(params: ExportCreateParams) {
    return this.client.request("POST", "/v1/exports", {
      body: {
        projectId: params.projectId,
        exportFormat: params.exportFormat ?? "json",
        includeUnapproved: params.includeUnapproved ?? false,
      },
    });
  }

  list(params: Record<string, unknown> = {}) {
    return this.client.request("GET", "/v1/exports", { query: params });
  }

  retrieve(exportId: string) {
    return this.client.request("GET", `/v1/exports/${exportId}`);
  }

  download(exportId: string) {
    return this.client.request("GET", `/v1/exports/${exportId}/download`);
  }
}
