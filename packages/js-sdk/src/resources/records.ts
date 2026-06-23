import type { ChemVault } from "../client.js";

export class RecordsResource {
  constructor(private readonly client: ChemVault) {}

  documentRecords(documentId: string, options: { includeUnapproved?: boolean } = {}) {
    return this.client.request("GET", `/v1/documents/${documentId}/records`, {
      query: { include_unapproved: options.includeUnapproved ?? false },
    });
  }

  chemicals(filters: Record<string, unknown> = {}) {
    return this.client.request("GET", "/v1/records/chemicals", { query: filters });
  }

  reactions(filters: Record<string, unknown> = {}) {
    return this.client.request("GET", "/v1/records/reactions", { query: filters });
  }

  measurements(filters: Record<string, unknown> = {}) {
    return this.client.request("GET", "/v1/records/measurements", { query: filters });
  }

  search(query: string, filters: Record<string, unknown> = {}) {
    return this.client.request("GET", "/v1/search", { query: { q: query, ...filters } });
  }
}
