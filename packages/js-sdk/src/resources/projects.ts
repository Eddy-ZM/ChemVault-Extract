import type { ChemVault } from "../client.js";

export type ProjectCreateParams = {
  name: string;
  workspaceId?: string;
};

export class ProjectsResource {
  constructor(private readonly client: ChemVault) {}

  list(params: Record<string, unknown> = {}) {
    return this.client.request("GET", "/v1/projects", { query: params });
  }

  create(params: ProjectCreateParams) {
    return this.client.request("POST", "/v1/projects", {
      body: { name: params.name, workspace_id: params.workspaceId },
    });
  }

  retrieve(projectId: string) {
    return this.client.request("GET", `/v1/projects/${projectId}`);
  }
}
