import assert from "node:assert/strict";
import { test } from "node:test";
import { ChemVault, ChemVaultError } from "../dist/index.js";

test("projects.list sends API key auth", async () => {
  const client = new ChemVault({
    apiKey: "cv_test_secret",
    baseUrl: "https://api.test",
    fetchImpl: async (url, init) => {
      assert.equal(url, "https://api.test/v1/projects");
      assert.equal(init.method, "GET");
      assert.equal(init.headers.get("authorization"), "Bearer cv_test_secret");
      return jsonResponse([{ id: "proj_1", name: "Organic synthesis" }]);
    },
  });

  const projects = await client.projects.list();

  assert.equal(projects[0].id, "proj_1");
});

test("documents.upload sends multipart form data", async () => {
  const client = new ChemVault({
    apiKey: "cv_test_secret",
    baseUrl: "https://api.test",
    fetchImpl: async (url, init) => {
      assert.equal(url, "https://api.test/v1/documents");
      assert.equal(init.method, "POST");
      assert.equal(init.headers.get("authorization"), "Bearer cv_test_secret");
      assert.ok(init.body instanceof FormData);
      assert.equal(init.body.get("project_id"), "proj_1");
      return jsonResponse({ document_id: "doc_1", status: "uploaded" }, 201);
    },
  });

  const document = await client.documents.upload({
    projectId: "proj_1",
    file: new Blob(["hello"], { type: "text/plain" }),
    filename: "notes.txt",
  });

  assert.equal(document.document_id, "doc_1");
});

test("API error payload becomes ChemVaultError", async () => {
  const client = new ChemVault({
    apiKey: "cv_test_secret",
    baseUrl: "https://api.test",
    fetchImpl: async () =>
      jsonResponse(
        { error: { code: "insufficient_scope", message: "Scope missing.", details: { scope: "projects:read" } } },
        403,
        { "x-request-id": "req_123" },
      ),
  });

  await assert.rejects(() => client.projects.list(), (error) => {
    assert.ok(error instanceof ChemVaultError);
    assert.equal(error.code, "insufficient_scope");
    assert.equal(error.statusCode, 403);
    assert.equal(error.requestId, "req_123");
    return true;
  });
});

function jsonResponse(payload, status = 200, headers = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}
