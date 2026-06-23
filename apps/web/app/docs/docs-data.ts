export type DocsSection = {
  id: string;
  title: string;
  body: string[];
  code?: {
    language: string;
    value: string;
  };
};

export type DocsPage = {
  slug: string;
  title: string;
  description: string;
  sections: DocsSection[];
};

export const docsPages: DocsPage[] = [
  {
    slug: "",
    title: "Documentation",
    description: "Guides for using ChemVault Extract and integrating the developer API.",
    sections: [
      {
        id: "overview",
        title: "Overview",
        body: [
          "ChemVault Extract turns scientific papers, lab reports, and instrument exports into structured, evidence-backed research databases.",
          "Use the product UI for upload, extraction, review, search, and export. Use the developer API when you need to connect ChemVault Extract to your own lab systems or research pipelines.",
        ],
      },
      {
        id: "quick-links",
        title: "Quick links",
        body: [
          "Start with Getting started for the product workflow, then read API authentication and API reference for developer integrations.",
        ],
      },
    ],
  },
  {
    slug: "getting-started",
    title: "Getting Started",
    description: "Create an account, upload a document, review extracted records, and export approved data.",
    sections: [
      {
        id: "workflow",
        title: "Core workflow",
        body: [
          "Create an account, create a project, upload a supported document, run extraction, review records, search the database, then export approved data.",
          "Extraction results remain in review. ChemVault Extract does not automatically approve AI-generated records.",
        ],
      },
      {
        id: "first-project",
        title: "First project",
        body: [
          "Open Dashboard, create or use the default project, then upload a PDF, TXT, CSV, XLSX, Markdown, or DOCX file. DOCX parsing can return a clear not-implemented message until full support is added.",
        ],
      },
    ],
  },
  {
    slug: "upload-documents",
    title: "Uploading Documents",
    description: "Supported files, storage behavior, parsing jobs, and upload API basics.",
    sections: [
      {
        id: "supported-files",
        title: "Supported files",
        body: ["ChemVault Extract accepts PDF, DOCX, CSV, XLSX, TXT, and Markdown uploads. Unsupported file extensions are rejected before storage."],
      },
      {
        id: "storage",
        title: "Storage and jobs",
        body: [
          "Uploaded files are saved to S3-compatible storage. Local development uses MinIO. Each upload creates a Document row and a queued parse job.",
        ],
      },
      {
        id: "api-upload",
        title: "API upload",
        body: ["Developer uploads use multipart/form-data and require documents:write scope."],
        code: {
          language: "bash",
          value: `curl -X POST https://api.chemvault.science/v1/documents \\
  -H "Authorization: Bearer cv_live_xxxxx" \\
  -F "project_id=proj_123" \\
  -F "file=@paper.pdf"`,
        },
      },
    ],
  },
  {
    slug: "ai-extraction",
    title: "AI Extraction",
    description: "Run structured extraction on selected chunks without bypassing cost and review controls.",
    sections: [
      {
        id: "selected-chunks",
        title: "Selected chunks only",
        body: [
          "AI extraction sends selected document chunks, not the full raw PDF. Chunk selection prioritizes scientific sections such as Experimental, Methods, Results, Supporting Information, and tables.",
        ],
      },
      {
        id: "cost-estimate",
        title: "Cost estimate",
        body: ["Estimate cost before extraction. Plan limits and monthly usage limits are checked before jobs are queued."],
        code: {
          language: "bash",
          value: `curl -X POST https://api.chemvault.science/v1/documents/doc_123/estimate \\
  -H "Authorization: Bearer cv_live_xxxxx"`,
        },
      },
    ],
  },
  {
    slug: "review-workflow",
    title: "Review Workflow",
    description: "Approve, edit, or reject evidence-backed extracted records.",
    sections: [
      {
        id: "review-status",
        title: "Review status",
        body: [
          "Records can be pending, needs_review, approved, or rejected. Valid normalization still does not auto-approve a record.",
          "Evidence quotes, page numbers, sections, confidence, and validation warnings are shown in the review UI.",
        ],
      },
    ],
  },
  {
    slug: "search",
    title: "Search",
    description: "Search documents, chunks, and reviewed scientific records.",
    sections: [
      {
        id: "product-search",
        title: "Product search",
        body: ["The product UI includes filters, evidence previews, and export actions for database search results."],
      },
      {
        id: "api-search",
        title: "API search",
        body: ["The developer search endpoint returns approved records by default."],
        code: {
          language: "bash",
          value: `curl "https://api.chemvault.science/v1/search?q=sodium%20hypochlorite" \\
  -H "Authorization: Bearer cv_live_xxxxx"`,
        },
      },
    ],
  },
  {
    slug: "export",
    title: "Export",
    description: "Export reviewed scientific records for downstream analysis.",
    sections: [
      {
        id: "formats",
        title: "Formats",
        body: ["ChemVault Extract supports export jobs for structured formats such as CSV, JSON, and XLSX. Exports should not include rejected records by default."],
      },
      {
        id: "api-export",
        title: "API export",
        body: ["Creating exports through the API requires exports:write scope and plan export permission."],
      },
    ],
  },
  {
    slug: "api",
    title: "Developer API",
    description: "Integrate scientific document extraction into your own workflows.",
    sections: [
      {
        id: "base-url",
        title: "Base URL",
        body: ["Use the production API base URL for external integrations."],
        code: { language: "text", value: "https://api.chemvault.science" },
      },
      {
        id: "workflow",
        title: "Example workflow",
        body: [
          "Create an API key, upload a document, poll the parse job, estimate AI extraction cost, run extraction, review records in the UI, then query approved records or create exports.",
        ],
      },
    ],
  },
  {
    slug: "api-authentication",
    title: "API Authentication",
    description: "Use scoped API keys for developer integrations.",
    sections: [
      {
        id: "headers",
        title: "Headers",
        body: ["Pass an API key using Authorization: Bearer or X-ChemVault-API-Key. API keys are shown only once and stored as hashes."],
        code: {
          language: "bash",
          value: `curl https://api.chemvault.science/v1/projects \\
  -H "Authorization: Bearer cv_live_xxxxx"`,
        },
      },
      {
        id: "scopes",
        title: "Scopes",
        body: [
          "Available scopes are projects:read, projects:write, documents:read, documents:write, extractions:read, extractions:write, records:read, exports:read, and exports:write.",
        ],
      },
    ],
  },
  {
    slug: "api-reference",
    title: "API Reference",
    description: "Core /v1 endpoints with scopes, examples, and response shapes.",
    sections: [
      {
        id: "projects",
        title: "Projects",
        body: ["GET /v1/projects requires projects:read. POST /v1/projects requires projects:write."],
      },
      {
        id: "documents",
        title: "Documents",
        body: ["POST /v1/documents uploads a file. GET /v1/documents/{document_id}/chunks returns parsed chunks."],
        code: {
          language: "python",
          value: `import requests

headers = {"Authorization": "Bearer cv_live_xxxxx"}
files = {"file": open("paper.pdf", "rb")}
data = {"project_id": "proj_123"}

response = requests.post(
    "https://api.chemvault.science/v1/documents",
    headers=headers,
    files=files,
    data=data,
)
print(response.json())`,
        },
      },
      {
        id: "extraction",
        title: "Extraction",
        body: ["POST /v1/documents/{document_id}/estimate estimates cost. POST /v1/documents/{document_id}/extract queues AI extraction."],
        code: {
          language: "json",
          value: `{
  "job_id": "job_123",
  "status": "queued",
  "estimated_cost_usd": 0.15625
}`,
        },
      },
      {
        id: "records",
        title: "Records",
        body: ["GET /v1/documents/{document_id}/records returns approved records by default. include_unapproved=true requires an additional extraction read scope."],
      },
      {
        id: "sdk-examples",
        title: "SDK examples",
        body: ["The SDKs call these same endpoints and use API key authentication."],
        code: {
          language: "ts",
          value: `const estimate = await client.documents.estimate("doc_123");
const job = await client.documents.extract("doc_123");
const records = await client.documents.records("doc_123");`,
        },
      },
    ],
  },
  {
    slug: "webhooks",
    title: "Webhooks",
    description: "Receive signed ChemVault events for document, extraction, review, export, and batch workflows.",
    sections: [
      {
        id: "events",
        title: "Events",
        body: [
          "Supported event types include document.uploaded, document.parsed, document.parse_failed, extraction.started, extraction.completed, extraction.failed, normalization.completed, normalization.failed, review.item_created, review.item_approved, review.item_rejected, export.completed, export.failed, batch.completed, batch.partial_failed, and batch.failed.",
          "Webhook payloads include ids and resource URLs or summaries. They do not include OpenAI API keys, passwords, full file contents, or large extracted record payloads by default.",
        ],
      },
      {
        id: "payload",
        title: "Payload format",
        body: ["Every webhook uses one event envelope."],
        code: {
          language: "json",
          value: `{
  "id": "evt_123",
  "type": "extraction.completed",
  "created_at": "2026-06-23T12:00:00Z",
  "workspace_id": null,
  "project_id": "proj_123",
  "document_id": "doc_123",
  "data": {
    "job_id": "job_123",
    "records_url": "/v1/documents/doc_123/records"
  },
  "api_version": "2026-06-01"
}`,
        },
      },
      {
        id: "signature",
        title: "Signature verification",
        body: [
          "ChemVault signs each delivery with HMAC SHA256. Use X-ChemVault-Timestamp, the raw request body, and your endpoint signing secret.",
        ],
        code: {
          language: "python",
          value: `import hmac
import hashlib

def verify_signature(secret, timestamp, body, signature):
    signed_payload = f"{timestamp}.{body}".encode()
    expected = hmac.new(
        secret.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"v1={expected}", signature)`,
        },
      },
      {
        id: "node-verification",
        title: "Node.js verification",
        body: ["Use a timing-safe comparison in Node.js receivers."],
        code: {
          language: "ts",
          value: `import crypto from "crypto";

function verifySignature(secret, timestamp, body, signature) {
  const payload = \`\${timestamp}.\${body}\`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");

  return crypto.timingSafeEqual(
    Buffer.from(\`v1=\${expected}\`),
    Buffer.from(signature),
  );
}`,
        },
      },
      {
        id: "retry-policy",
        title: "Retry policy",
        body: [
          "ChemVault attempts delivery immediately, then retries after 1 minute, 5 minutes, 30 minutes, and 2 hours. After five attempts the delivery is marked failed.",
          "2xx responses mark a delivery delivered. 4xx, 5xx, and timeout responses are retried. Response body previews are capped at 2,000 characters.",
        ],
      },
    ],
  },
  {
    slug: "sdks",
    title: "SDKs",
    description: "Use local Python and JavaScript SDK packages to call the existing /v1 API.",
    sections: [
      {
        id: "publishing",
        title: "Publishing status",
        body: [
          "Package publishing is not enabled yet. Use local package installation during development.",
          "SDKs use API key authentication and do not bypass plan limits, rate limits, evidence checks, or review workflows.",
        ],
      },
      {
        id: "packages",
        title: "Packages",
        body: ["Python source lives in packages/python-sdk. JavaScript source lives in packages/js-sdk."],
      },
    ],
  },
  {
    slug: "sdks/python",
    title: "Python SDK",
    description: "Upload documents, run extraction, query records, and create exports from Python.",
    sections: [
      {
        id: "install",
        title: "Install",
        body: ["Package publishing is not enabled yet. Use local package installation during development."],
        code: { language: "bash", value: "pip install -e packages/python-sdk" },
      },
      {
        id: "usage",
        title: "Usage",
        body: ["Initialize the client with an API key. The SDK calls the existing /v1 API."],
        code: {
          language: "python",
          value: `from chemvault import ChemVault

client = ChemVault(api_key="cv_live_xxx")
project = client.projects.create(name="Organic synthesis")
document = client.documents.upload(
    project_id=project.id,
    file_path="paper.pdf",
)
estimate = client.documents.estimate(document.id)
job = client.documents.extract(document.id)
records = client.documents.records(document.id)`,
        },
      },
      {
        id: "errors",
        title: "Errors",
        body: ["API error responses are raised as ChemVaultError with code, status_code, details, and request_id."],
      },
    ],
  },
  {
    slug: "sdks/javascript",
    title: "JavaScript SDK",
    description: "Use the TypeScript SDK from Node.js or browser-capable upload flows.",
    sections: [
      {
        id: "install",
        title: "Install",
        body: ["Package publishing is not enabled yet. Use local package installation during development."],
        code: { language: "bash", value: "npm install ./packages/js-sdk" },
      },
      {
        id: "usage",
        title: "Usage",
        body: ["The SDK is fetch-based and supports custom baseUrl for self-hosted deployments."],
        code: {
          language: "ts",
          value: `import { ChemVault } from "@chemvault/sdk";

const client = new ChemVault({ apiKey: "cv_live_xxx" });
const project = await client.projects.create({ name: "Organic synthesis" });
const document = await client.documents.upload({
  projectId: project.id,
  file,
});
const estimate = await client.documents.estimate(document.id);
const job = await client.documents.extract(document.id);
const records = await client.documents.records(document.id);`,
        },
      },
      {
        id: "errors",
        title: "Errors",
        body: ["API error responses become ChemVaultError instances with code, statusCode, details, and requestId."],
      },
    ],
  },
  {
    slug: "errors",
    title: "Errors",
    description: "The /v1 API uses one consistent error envelope.",
    sections: [
      {
        id: "format",
        title: "Error format",
        body: ["Every /v1 error returns an error object with code, message, and details."],
        code: {
          language: "json",
          value: `{
  "error": {
    "code": "monthly_limit_reached",
    "message": "Monthly AI extraction limit reached.",
    "details": {}
  }
}`,
        },
      },
      {
        id: "codes",
        title: "Common codes",
        body: [
          "Common codes include unauthorized, forbidden, not_found, invalid_request, validation_error, rate_limit_exceeded, monthly_limit_reached, missing_openai_key, api_key_revoked, api_key_expired, and insufficient_scope.",
        ],
      },
    ],
  },
  {
    slug: "rate-limits",
    title: "Rate Limits",
    description: "API limits are enforced per user or API key using Redis-backed counters.",
    sections: [
      {
        id: "plans",
        title: "Plan limits",
        body: [
          "Free plans receive 60 requests per minute and 1,000 requests per day. Student plans receive 120 per minute and 5,000 per day. Researcher plans receive 300 per minute and 20,000 per day. Lab plans receive 600 per minute and 100,000 per day.",
        ],
      },
      {
        id: "response",
        title: "429 response",
        body: ["When a limit is exceeded, the API returns rate_limit_exceeded."],
        code: {
          language: "json",
          value: `{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please try again later.",
    "details": {}
  }
}`,
        },
      },
    ],
  },
  {
    slug: "security",
    title: "Security",
    description: "Security controls for API keys, documents, extraction, and records.",
    sections: [
      {
        id: "keys",
        title: "API keys",
        body: [
          "Raw API keys are shown only once. The backend stores key hashes, prefixes, masked keys, scopes, expiry, and revocation timestamps.",
          "API keys cannot manage billing, create new API keys, or modify user account credentials.",
        ],
      },
      {
        id: "data",
        title: "Data controls",
        body: [
          "Developer API calls respect project and workspace permissions. AI extraction sends selected chunks, not full raw PDF files.",
        ],
      },
    ],
  },
  {
    slug: "self-hosting",
    title: "Self Hosting",
    description: "Run the MVP stack locally with Docker Compose and environment variables.",
    sections: [
      {
        id: "services",
        title: "Services",
        body: ["Local development uses Next.js, FastAPI, PostgreSQL, Redis, MinIO, and a Python worker."],
      },
      {
        id: "environment",
        title: "Environment",
        body: ["Configure DATABASE_URL, REDIS_URL, S3 settings, JWT_SECRET, APP_ENCRYPTION_KEY, OPENAI_API_KEY, and Stripe price IDs as needed."],
      },
    ],
  },
];

export function getDocsPage(slug: string): DocsPage | undefined {
  return docsPages.find((page) => page.slug === slug);
}
