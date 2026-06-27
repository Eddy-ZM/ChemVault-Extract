# ChemVault Extract

Production-ready MVP foundation for ingesting chemistry papers, lab reports, and instrument-exported files into an AI Scientific Data Extraction / Research Intelligence pipeline.

This project uses OpenAI API structured outputs for the AI extraction mode. It includes the monorepo, Next.js frontend, FastAPI backend, PostgreSQL models, MinIO file storage, Redis job queue, a Python parsing worker, and a cost-controlled structured-extraction pipeline.

## Services

- `web`: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui-style components
- `api`: FastAPI service with upload, document, job, and health endpoints
- `worker`: Python Redis worker, packaged from `services/worker`, that parses uploaded files into pages, blocks, table blocks, and chunks, then runs structured extraction against selected chunks
- `postgres`: application database
- `redis`: extraction job queue
- `minio`: S3-compatible object storage

## Local Setup

Prerequisites:

- Docker and Docker Compose
- Node.js 22+ and Python 3.12 if running services outside Docker

From this directory:

```bash
cp .env.example .env
# Edit .env and set JWT_SECRET plus APP_ENCRYPTION_KEY before registering users.
docker compose up --build
```

If you are reusing a local Docker volume from an earlier schema, reset it before testing the parsing or extraction layers:

```bash
docker compose down -v
docker compose up --build
```

Open:

- Frontend: [http://localhost:3000](http://localhost:3000)
- API health: [http://localhost:8000/health](http://localhost:8000/health)
- MinIO console: [http://localhost:9001](http://localhost:9001)

Default MinIO credentials are `chemvault` / `chemvault-secret`.

## Test Upload

1. Open [http://localhost:3000/documents/upload](http://localhost:3000/documents/upload).
2. Upload a supported file: PDF, DOCX, CSV, XLSX, TXT, or MD.
3. The upload page shows the created document ID and extraction job ID.
4. Open the document detail page to watch the worker update the job status and parsed preview.
5. Use the `Preview`, `Pages`, `Blocks`, and `Chunks` tabs to inspect parser output.
6. Click `Estimate AI Cost` to preview selected chunks, model, and estimated OpenAI cost.
7. Click `Run AI Extraction` to run the structured extraction pipeline. This requires `OPENAI_API_KEY`.
8. Open `/documents/{document_id}/review` to inspect review items.
9. Confirm the object exists in MinIO under the `chemvault-documents` bucket.

Check API health directly:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok" }
```

## API Endpoints

- `GET /health`
- `POST /contact`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /projects`
- `POST /projects`
- `GET /workspaces`
- `POST /workspaces`
- `GET /workspaces/{workspace_id}`
- `PATCH /workspaces/{workspace_id}`
- `DELETE /workspaces/{workspace_id}`
- `POST /workspaces/{workspace_id}/invites`
- `GET /workspaces/{workspace_id}/members`
- `PATCH /workspaces/{workspace_id}/members/{member_id}`
- `DELETE /workspaces/{workspace_id}/members/{member_id}`
- `POST /workspaces/invites/{invite_id}/accept`
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /documents/upload`
- `POST /documents/batch-upload`
- `POST /documents/{document_id}/extract`
- `POST /documents/{document_id}/extract-ai`
- `POST /documents/batch-extract-ai`
- `GET /documents/{document_id}/pages`
- `GET /documents/{document_id}/blocks`
- `GET /documents/{document_id}/tables`
- `GET /documents/{document_id}/chunks`
- `GET /documents/{document_id}/extractions`
- `GET /documents/{document_id}/review-items`
- `POST /documents/{document_id}/normalize`
- `GET /documents/{document_id}/normalized-records`
- `POST /records/{record_type}/{record_id}/renormalize`
- `GET /usage/current-month`
- `GET /billing/subscription`
- `POST /billing/create-checkout-session`
- `POST /billing/create-portal-session`
- `POST /webhooks/stripe`
- `GET /settings/ai`
- `POST /settings/ai`
- `POST /settings/ai/test-openai-key`
- `DELETE /settings/ai/openai-key`
- `GET /settings/api-keys`
- `POST /settings/api-keys`
- `POST /settings/api-keys/{api_key_id}/revoke`
- `GET /settings/webhooks`
- `POST /settings/webhooks`
- `GET /settings/webhooks/{webhook_endpoint_id}`
- `PATCH /settings/webhooks/{webhook_endpoint_id}`
- `DELETE /settings/webhooks/{webhook_endpoint_id}`
- `POST /settings/webhooks/{webhook_endpoint_id}/rotate-secret`
- `POST /settings/webhooks/{webhook_endpoint_id}/test`
- `GET /settings/webhooks/{webhook_endpoint_id}/deliveries`
- `GET /settings/webhooks/deliveries/{delivery_id}`
- `GET /developers/logs`
- `GET /developers/usage`
- `GET /exports`
- `POST /exports`
- `GET /database`
- `GET /search`
- `GET /batch/jobs`
- `GET /batch/jobs/{batch_job_id}`
- `POST /batch/jobs/{batch_job_id}/cancel`
- `POST /batch/jobs/{batch_job_id}/retry-failed`
- `POST /batch/extract-ai`
- `GET /admin/users`
- `GET /admin/usage`
- `POST /admin/users/{user_id}/plan`
- `GET /jobs/{job_id}`
- `GET /review-items`
- `PATCH /review-items/{review_item_id}`

Developer API endpoints:

- `GET /v1/projects`
- `POST /v1/projects`
- `GET /v1/projects/{project_id}`
- `POST /v1/documents`
- `GET /v1/documents`
- `GET /v1/documents/{document_id}`
- `GET /v1/documents/{document_id}/status`
- `GET /v1/documents/{document_id}/chunks`
- `POST /v1/documents/{document_id}/estimate`
- `POST /v1/documents/{document_id}/extract`
- `GET /v1/jobs/{job_id}`
- `GET /v1/documents/{document_id}/records`
- `GET /v1/records/chemicals`
- `GET /v1/records/reactions`
- `GET /v1/records/measurements`
- `GET /v1/search`
- `POST /v1/exports`
- `GET /v1/exports`
- `GET /v1/exports/{export_id}`
- `GET /v1/exports/{export_id}/download`
- `GET /v1/usage`

## Database Foundation

Core tables:

- `projects`
- `users`
- `user_ai_settings`
- `ai_usage_records`
- `subscriptions`
- `billing_events`
- `audit_logs`
- `api_keys`
- `api_request_logs`
- `webhook_endpoints`
- `webhook_deliveries`
- `workspaces`
- `workspace_members`
- `batch_jobs`
- `batch_job_items`
- `contact_messages`
- `documents`
- `document_pages`
- `document_blocks`
- `document_chunks`
- `extraction_jobs`
- `extraction_runs`
- `chemical_entities`
- `reaction_records`
- `measurement_records`
- `review_items`
- `export_jobs`

Future extracted records include an `evidence` JSON column so chemistry entities, reactions, and measurements can point back to source pages, sections, and quotes.

Example evidence payload:

```json
{
  "page": 3,
  "section": "Experimental",
  "quote": "The product was obtained in 82% yield."
}
```

## Public Product Site

ChemVault Extract includes a public SaaS site in the same Next.js app. Public pages do not require login:

- `/`
- `/features`
- `/pricing`
- `/demo`
- `/use-cases`
- `/security`
- `/docs`
- `/contact`
- `/login`
- `/register`

The public navigation is separate from the authenticated application shell. Dashboard, documents, database, search, exports, workspaces, usage, settings, and account pages remain protected by JWT middleware.

Public page highlights:

- Home explains the product positioning: turning papers, lab reports, and instrument exports into structured, evidence-backed research databases.
- Features describes ingestion formats, AI structured extraction, evidence, normalization, review, search/export, and team workspaces.
- Demo is a static product demo using clearly labelled sample data. It does not call the API and does not claim to be a real extraction result.
- Security explains project isolation, team permissions, selected-chunk AI extraction, encrypted user OpenAI keys, masked API key display, Stripe billing, and user export control. It intentionally does not claim SOC2, HIPAA, ISO, or other compliance certifications.
- Docs is a documentation site with a left sidebar, code examples, API authentication, API reference, error format, rate limits, security notes, and self-hosting guidance.
- Contact saves messages to the `contact_messages` table through `POST /contact`. It does not send email yet.

Product polish added to the authenticated app:

- Dashboard quick actions for upload, batch extraction, review, search, and export.
- Documents table with file-type icons, project IDs, parsing/extraction/review statuses, and action buttons.
- Document detail timeline: uploaded, parsed, AI extracted, normalized, reviewed, exported.
- Review page for pending review items across accessible documents.
- Search page with filters sidebar, result counts, record-type tabs, evidence previews, and export CTA.
- Exports page with CSV/JSON/XLSX format cards, export history, status badges, download actions, and review warning.

## Parsing Pipeline

The first-stage worker parses uploaded files into normalized pages/blocks/chunks.
In AI mode, the same worker then runs OpenAI extraction and a normalization/enrichment pass.

For each queued job, the worker:

1. Pops the job ID from Redis.
2. Updates the job to `parsing`.
3. Downloads the original object from MinIO / S3-compatible storage.
4. Selects a parser by file type.
5. Saves `DocumentPage`, `DocumentBlock`, and `DocumentChunk` rows.
6. Updates the job and document to `review_ready`.
7. Marks failures as `failed` with a clear error message.

Supported parser inputs:

- TXT / MD: reads plain text, detects Markdown and scientific headings, creates page 1, paragraph blocks, and section-based chunks.
- CSV: reads tabular data with pandas when available, stores a table block with rows JSON, and creates a table-oriented chunk with column names and sample rows.
- XLSX: reads each sheet, creates one table block per sheet, stores `sheet_name` in metadata, and creates chunks for each sheet table.
- PDF: attempts Docling if installed, otherwise falls back to `pypdf`; scanned PDFs without extractable text fail with `No extractable text found. OCR support will be added in a later stage.`
- DOCX: extracts headings and paragraphs with `python-docx`.

Scientific section detection recognizes Abstract, Introduction, Background, Experimental, Materials and Methods, Methods, Results, Discussion, Conclusion, Supporting Information, References, and related variants. Chunks are grouped by section and References are excluded from future extraction chunks.

Sample inputs live in `samples/`:

- `samples/sample_lab_report.txt`
- `samples/sample_table.csv`
- `samples/sample_workbook.xlsx`
- `samples/sample_paper_like.txt`

To test each type locally, start Docker Compose, upload one sample at a time from `/documents/upload`, then open the document detail page. TXT and MD should show detected sections, CSV should show a table block and table chunk, and XLSX should show one table block per sheet. For PDF testing, upload a small text-based PDF; scanned PDFs are expected to fail until OCR support is added.

## Structured Extraction Foundation

The extraction layer uses `AI_PROVIDER=openai` by default. It sends only selected `DocumentChunk` text to OpenAI, never the original PDF or full uploaded object. AI extraction is protected by JWT auth, project ownership checks, and monthly usage limits.

Users can run extraction with either:

- Platform key: server-side `OPENAI_API_KEY`.
- User key: encrypted per-user key saved through `/settings/ai`.

If a required key is missing, the API returns `Platform OpenAI API key is missing.` or `User OpenAI API key is missing.`

OpenAI API usage is metered. Use `POST /documents/{document_id}/estimate-ai-cost` or the `Estimate AI Cost` button before running extraction.

Configure API access in `.env`:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4
OPENAI_FALLBACK_MODEL=gpt-5.5
AI_ENABLE_FALLBACK_MODEL=false
```

When the user clicks `Run AI Extraction`, the API creates an `ai_extraction` job. The worker:

1. Requires existing parsed `DocumentChunk` rows before creating the AI job.
2. Selects at most `AI_MAX_CHUNKS_PER_DOCUMENT` chunks by section priority.
3. Truncates each selected chunk to `AI_MAX_CHUNK_CHARS`.
4. Moves the job through `extracting`, `validating`, `normalizing`, and `review_ready`.
5. Runs the four extractor interfaces:
   - `metadata`
   - `chemical_entities`
   - `reactions`
   - `measurements`
6. Saves one `ExtractionRun` per extractor with provider, model, selected chunk IDs, estimated tokens, estimated cost, raw output, and parsed output.

Chunk selection priority:

1. Experimental
2. Materials and Methods
3. Methods
4. Results
5. Supporting Information
6. Tables
7. Abstract
8. Introduction

References are excluded. Long chunks are truncated and recorded with `truncated`, `original_chars`, and `used_chars` metadata in the run payload.

Cost estimates use centralized prices in `services/api/app/config/ai.py`:

- `gpt-4.1-mini`: input `$0.40 / 1M`, output `$1.60 / 1M`
- `gpt-5.4`: input `$5.00 / 1M`, output `$30.00 / 1M`

The extractor modules live in `services/api/app/extractors`:

- `schemas.py`: JSON-schema-ready Pydantic models for metadata, chemical entities, reactions, measurements, and evidence.
- `prompts.py`: the system prompt for strict source-grounded extraction.
- `base.py`: extractor interface and chunk selection.
- `metadata_extractor.py`, `chemical_extractor.py`, `reaction_extractor.py`, `measurement_extractor.py`: extractor-specific section targeting.
- `openai_client.py`: OpenAI Responses API structured-output client.
- `pipeline.py`: orchestrates OpenAI calls, schema validation, fallback handling, record persistence, and review item creation.

The validation modules live in `services/api/app/validators`:

- `evidence_validator.py`: checks `document_id`, `chunk_id`, page range, and whether `quote` appears in the chunk text.
- `chemistry_validator.py`: confidence and chemistry-specific validation checks.
- `normalizers/`: raw/normalized reconciliation for chemical, reaction, and measurement records.

Review UI is available at `/documents/{document_id}/review`. It can list review items, approve, reject, and edit `extractedData`. AI output is schema-validated before records are written, and evidence quotes are checked against the source chunk before review status is assigned.

Fallback model behavior is disabled by default. Set `AI_ENABLE_FALLBACK_MODEL=true` to retry once with `OPENAI_FALLBACK_MODEL` when the default model call or schema validation fails. Fallback attempts are recorded as `ExtractionRun` rows.

## Scientific Validation + Normalization

After every successful AI extraction cycle, the worker normalizes all structured records and writes both raw + normalized values.

Normalization rules include:

- Chemical names and role normalization (e.g. `EtOH -> ethanol`, `NaOCl -> sodium hypochlorite`).
- Optional `PubChem` enrichment (`pubchem_name` lookup) for compounds:
  - `PubChem` found: `pubchemCid`, `canonicalSmiles`, `inchi`, `inchiKey`, `molecularFormula`, `molecularWeight` saved.
  - `not_found`: status is `not_found`, record is still kept and marked for review.
  - API/parse errors: status is `error`, warning is recorded, pipeline continues.
- Optional RDKit validation of canonical SMILES (`rdkit_available=false` when dependency is missing).
- Reaction yield, temperature, and time canonicalization.
- Measurement type/unit/value normalization and warning generation.

No record is auto-approved after normalization. Review items remain `pending`/`needs_review` and still require human approval in the `/documents/{document_id}/review` UI.

## API endpoints

- `POST /documents/{document_id}/normalize` (normalize extracted records for a document).
- `GET /documents/{document_id}/normalized-records` (read normalized records).
- `POST /records/{record_type}/{record_id}/renormalize` (re-run normalization for a single record).

## Authentication, Usage, Billing, And API Keys

ChemVault Extract uses ChemVault User Center as the primary account system. Public `/login` and `/register` pages redirect to `user.chemvault.science` with a `returnTo` URL, and the backend accepts the shared `chemvault_session` httpOnly cookie. Anonymous users cannot upload documents or run AI extraction.

The legacy Extract JWT login/register endpoints remain available for local compatibility and tests, but production sign-in should go through User Center. The web app stores only a cached current-user profile in browser storage for client navigation state. The backend remains the source of truth for every protected request.

Register and login:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "content-type: application/json" \
  -d '{"email":"you@example.com","password":"change-me-123","name":"Your Name"}'

curl -X POST http://localhost:8000/auth/login \
  -H "content-type: application/json" \
  -d '{"email":"you@example.com","password":"change-me-123"}'
```

Use the returned token:

```bash
curl http://localhost:8000/documents \
  -H "authorization: Bearer <access_token>"
```

Every project belongs to a user. Documents, jobs, review items, extracted records, usage records, and exports are only accessible through the owning user's projects. Accessing another user's document ID returns `403`.

User Center integration:

```bash
NEXT_PUBLIC_CHEMVAULT_USER_URL=https://user.chemvault.science
CHEMVAULT_USER_BASE_URL=https://user.chemvault.science
CHEMVAULT_USER_COOKIE_NAME=chemvault_session
CHEMVAULT_USER_COOKIE_DOMAIN=.chemvault.science
CHEMVAULT_USER_SERVICE_KEY=chemvault_extract
CHEMVAULT_USER_REQUIRE_SERVICE_ACCESS=false
```

When a shared User Center session first reaches the FastAPI backend, Extract validates it against `/api/auth/me`, creates or updates the local `User` row by email, and creates the default local project/subscription/settings if needed. Existing Extract billing, usage, and project data are not overwritten by User Center profile sync. Set `CHEMVAULT_USER_REQUIRE_SERVICE_ACCESS=true` to additionally require User Center service access for `chemvault_extract`.

Registration can be protected by Cloudflare Turnstile. Configure the browser-visible site key in the frontend and the secret key in the FastAPI environment:

```bash
NEXT_PUBLIC_TURNSTILE_SITE_KEY=0x...
TURNSTILE_SECRET_KEY=0x...
TURNSTILE_REQUIRED=true
```

When `TURNSTILE_REQUIRED=true`, `/auth/register` rejects requests that do not include a valid Turnstile response token. Local development can leave `TURNSTILE_REQUIRED=false`.

Monthly AI limits are enforced before creating an AI extraction job:

- File limit: plan `monthlyAiFileLimit`.
- Platform cost limit: plan `monthlyAiCostLimitUsd`.
- User-provided OpenAI keys do not count against platform AI cost, but still count against monthly file, project, document, and storage limits.
- Uploads are checked against plan `maxDocuments` and `maxStorageMb`.
- Project creation is checked against `maxProjects`.
- Export creation is checked against `canExport`.
- Batch extraction is reserved for plans with `canBatchExtract=true`.

Current usage:

```bash
curl http://localhost:8000/usage/current-month \
  -H "authorization: Bearer <access_token>"
```

User OpenAI keys are encrypted with `APP_ENCRYPTION_KEY`. The API never returns the full key; `/settings/ai` only returns a masked key such as `sk-****abcd`. If `APP_ENCRYPTION_KEY` is missing, saving user-provided OpenAI keys is rejected. Set `ALLOW_USER_OPENAI_KEYS=false` to force platform-key mode.

Admin-only APIs:

- `GET /admin/users`
- `GET /admin/usage`
- `POST /admin/users/{user_id}/plan`

Only users with `role = admin` can access them.

`POST /admin/users/{user_id}/plan` sets a local `planOverride` for testing and records an audit log. It does not modify Stripe subscriptions.

## Developer API Access

ChemVault Extract exposes a scoped `/v1` developer API for server-side integrations. Users create API keys from `/settings/api-keys`; raw keys are shown once, then only a masked key such as `cv_live_****abcd` is returned.

Security rules:

- API keys are stored as hashes. Raw keys are never saved.
- Revoked and expired keys return `401`.
- Missing scopes return `403` with `insufficient_scope`.
- API key requests still enforce project/workspace permissions, plan limits, storage limits, monthly extraction limits, and review/evidence rules.
- API keys cannot manage billing, create other API keys, or change user account credentials.
- `/v1/search` and `/v1/documents/{document_id}/records` return approved records by default. `include_unapproved=true` requires additional extraction read scope and still marks unapproved records in the response.

Available scopes:

- `projects:read`
- `projects:write`
- `documents:read`
- `documents:write`
- `extractions:read`
- `extractions:write`
- `records:read`
- `exports:read`
- `exports:write`

API upload example:

```bash
curl -X POST https://api.chemvault.science/v1/documents \
  -H "Authorization: Bearer cv_live_xxxxx" \
  -F "project_id=proj_123" \
  -F "file=@paper.pdf"
```

Estimate and run extraction:

```bash
curl -X POST https://api.chemvault.science/v1/documents/doc_123/estimate \
  -H "Authorization: Bearer cv_live_xxxxx"

curl -X POST https://api.chemvault.science/v1/documents/doc_123/extract \
  -H "Authorization: Bearer cv_live_xxxxx" \
  -H "content-type: application/json" \
  -d '{"mode":"standard"}'
```

Search approved records:

```bash
curl "https://api.chemvault.science/v1/search?q=NaOCl" \
  -H "Authorization: Bearer cv_live_xxxxx"
```

Unified `/v1` error format:

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please try again later.",
    "details": {}
  }
}
```

Rate limits are Redis-backed and keyed by user or API key:

| Plan | Requests/min | Requests/day |
|---|---:|---:|
| Free | 60 | 1,000 |
| Student | 120 | 5,000 |
| Researcher | 300 | 20,000 |
| Lab | 600 | 100,000 |

API request logs are available from `/developers/logs` and are saved in `api_request_logs` with request id, method, path, status, latency, IP, and user agent. Logs do not store raw API keys, uploaded file contents, or OpenAI API keys.

FastAPI OpenAPI output is available when `ENABLE_API_DOCS=true`. Admin routes are excluded from the generated schema.

## Webhooks

Webhook settings are available at `/settings/webhooks` and stored in `webhook_endpoints`. Each endpoint has a signing secret that is shown only when the endpoint is created or rotated. The database stores a hash, encrypted secret, and preview such as `whsec_****abcd`; it does not store the raw secret as plain text.

Supported events:

- `document.uploaded`
- `document.parsed`
- `document.parse_failed`
- `extraction.started`
- `extraction.completed`
- `extraction.failed`
- `normalization.completed`
- `normalization.failed`
- `review.item_created`
- `review.item_approved`
- `review.item_rejected`
- `export.completed`
- `export.failed`
- `batch.completed`
- `batch.partial_failed`
- `batch.failed`

Delivery headers:

- `X-ChemVault-Event`
- `X-ChemVault-Delivery`
- `X-ChemVault-Timestamp`
- `X-ChemVault-Signature`

The signature is `v1=` plus `HMAC_SHA256(secret, f"{timestamp}.{raw_body}")`. Verify the exact raw request body before parsing JSON.

Retry policy:

| Attempt | Delay |
|---:|---|
| 1 | Immediately |
| 2 | 1 minute |
| 3 | 5 minutes |
| 4 | 30 minutes |
| 5 | 2 hours |

Webhook failures do not block document parsing, extraction, normalization, review, export, or batch processing. Failed deliveries are saved in `webhook_deliveries` with a response body preview capped at 2,000 characters.

Local webhook testing:

```bash
docker compose up postgres redis minio api worker
ngrok http 8001
```

Create a webhook endpoint pointing to the HTTPS forwarding URL, then click “Send test event” on `/settings/webhooks`. The worker also processes queued deliveries from `WEBHOOK_DELIVERY_QUEUE`.

## SDK Local Development

The SDKs are local packages for now. Publishing to PyPI and npm is not enabled yet.

Python SDK:

```bash
cd packages/python-sdk
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

```python
from chemvault import ChemVault

client = ChemVault(api_key="cv_live_xxx", base_url="https://api.chemvault.science")
project = client.projects.create(name="Organic synthesis")
document = client.documents.upload(project_id=project.id, file_path="paper.pdf")
estimate = client.documents.estimate(document.document_id)
job = client.documents.extract(document.document_id)
records = client.documents.records(document.document_id)
```

JavaScript SDK:

```bash
npm install ./packages/js-sdk
```

```ts
import { ChemVault } from "@chemvault/sdk";

const client = new ChemVault({ apiKey: "cv_live_xxx" });
const project = await client.projects.create({ name: "Organic synthesis" });
const document = await client.documents.upload({
  projectId: project.id,
  file,
  filename: "paper.pdf",
});
const estimate = await client.documents.estimate(document.document_id);
const job = await client.documents.extract(document.document_id);
const records = await client.documents.records(document.document_id);
```

Both SDKs call the existing `/v1` API and use API key authentication. They do not bypass API scopes, plan limits, rate limits, selected-chunk extraction, evidence validation, normalization, or review workflows. They do not store or send user OpenAI API keys.

## Stripe Billing

Stripe is the source of truth for paid subscription state. The local `subscriptions` table caches Stripe state for fast plan enforcement, and `billing_events` prevents duplicate webhook processing.

Plans are centralized in `services/api/app/billing/plans.py`:

| Plan | AI files/month | Platform AI cost | Projects | Documents | Storage | Export | Batch | Team |
|---|---:|---:|---:|---:|---:|---|---|---:|
| Free | 10 | $5 | 2 | 50 | 500 MB | Yes | No | 1 |
| Student | 100 | $20 | 10 | 1,000 | 5 GB | Yes | No | 1 |
| Researcher | 500 | $100 | 50 | 10,000 | 50 GB | Yes | Yes | 1 |
| Lab | 3,000 | $500 | 200 | 100,000 | 500 GB | Yes | Yes | 10 |

Create Stripe Products and recurring Prices for Student, Researcher, and Lab, each with monthly and yearly intervals. Put the resulting price IDs in `.env`:

```bash
STRIPE_PRICE_STUDENT_MONTHLY=price_...
STRIPE_PRICE_RESEARCHER_MONTHLY=price_...
STRIPE_PRICE_LAB_MONTHLY=price_...
STRIPE_PRICE_STUDENT_YEARLY=price_...
STRIPE_PRICE_RESEARCHER_YEARLY=price_...
STRIPE_PRICE_LAB_YEARLY=price_...
```

Checkout:

```bash
curl -X POST http://localhost:8000/billing/create-checkout-session \
  -H "authorization: Bearer <access_token>" \
  -H "content-type: application/json" \
  -d '{"plan":"researcher","billing_interval":"monthly"}'
```

The frontend `/pricing` page calls this endpoint and redirects to the returned Stripe Checkout URL. Free does not use checkout.

Customer Portal:

```bash
curl -X POST http://localhost:8000/billing/create-portal-session \
  -H "authorization: Bearer <access_token>"
```

The frontend `/account/billing` page uses Stripe Customer Portal for subscription and billing-detail management. Invoice PDF download, tax/VAT, coupons, and metered billing are intentionally not implemented.

Webhook local testing:

```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
```

Copy the printed webhook signing secret into:

```bash
STRIPE_WEBHOOK_SECRET=whsec_...
```

Handled events:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

All webhook requests verify the `Stripe-Signature` header against `STRIPE_WEBHOOK_SECRET` using the raw request body. Paid plans are only applied after a valid Stripe webhook confirms an `active` or `trialing` subscription. `past_due`, `unpaid`, `cancelled`, deleted, or expired subscriptions are downgraded or restricted to free plan limits unless an admin `planOverride` is present.

Plan enforcement is implemented in `services/api/app/billing/enforcement.py`. Test it by creating a free user, uploading documents until the document/storage limit is reached, creating projects until the project limit is reached, and trying AI extraction after monthly file or platform-cost limits are exhausted.

## Team Workspace + Batch Extraction

Team workspaces let Lab and admin users share projects without weakening project isolation. Personal projects have `userId` set and `workspaceId = null`. Team projects have `workspaceId` set and are accessible only through active `WorkspaceMember` records.

Workspace roles:

- `owner`: all workspace permissions, billing owner, and workspace deletion.
- `admin`: manage workspace members, create projects, upload, extract, review, and export.
- `member`: upload documents, run extraction, review, and export inside existing workspace projects.
- `viewer`: read-only access to workspace projects and records.

Invites are stored as `WorkspaceMember` rows with status `invited`; email delivery is intentionally not implemented yet. Use the returned invite token or invite ID with `POST /workspaces/invites/{invite_id}/accept`.

Frontend pages:

- `/workspaces`
- `/workspaces/new`
- `/workspaces/{workspace_id}`
- `/workspaces/{workspace_id}/members`
- `/projects/new`
- `/documents/batch-upload`
- `/batch`
- `/batch/{batch_job_id}`
- `/database`
- `/search`

Batch upload:

1. Create a project from `/projects/new`.
2. Open `/documents/batch-upload`.
3. Select a project and multiple supported files.
4. The API creates one `BatchJob`, one `Document` per file, one parse `ExtractionJob` per file, and one `BatchJobItem` per file.
5. The worker updates each batch item and recalculates batch progress as parse jobs finish.

Batch AI extraction:

1. Requires a Researcher, Lab, admin, or plan override with `canBatchExtract=true`.
2. Open `/batch`.
3. Select a project and either selected documents or all unprocessed documents.
4. The API estimates aggregate selected-chunk cost, checks monthly file/cost limits, creates a batch job, creates one AI extraction job per document, and pushes those jobs to Redis.
5. `/batch/{batch_job_id}` shows progress, failed items, cancel-queued, and retry-failed controls.

Batch extraction never sends raw uploaded files or entire PDFs to OpenAI. It uses the same selected `DocumentChunk` cost controls as single-document extraction. User-provided OpenAI keys still count toward monthly file limits, storage limits, document limits, and batch plan limits.

Useful local checks:

```bash
pytest services/api/tests/test_api.py -q
npm run build -w apps/web
```

Standalone user account site:

- Path: `/Users/edwardmu/ChemVault_suite/ChemVault-user`
- Open `index.html` or serve the directory as static files.
- It manages login/register, account details, current-month usage, and user OpenAI key settings against the configured FastAPI API base URL.

## Local Development Without Docker

Install frontend dependencies:

```bash
npm install
npm run dev
```

Run the API locally:

```bash
cd services/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

Run the worker locally in a second shell:

```bash
cd services/api
. .venv/bin/activate
python -m app.workers.worker
```

For non-Docker frontend development, set `API_BASE_URL=http://localhost:8000` in `.env`.

## Environment Variables

- `DATABASE_URL`: SQLAlchemy database URL for PostgreSQL.
- `APP_URL`: Canonical app URL, for example `https://app.chemvault.science`.
- `NODE_ENV`: Runtime environment.
- `CORS_ALLOWED_ORIGINS`: Comma-separated allowed browser origins. Use the app domain only in production.
- `HYPERDRIVE_BINDING`: Optional Cloudflare Hyperdrive binding name if a Worker directly connects to PostgreSQL.
- `HYPERDRIVE_DATABASE_URL`: Optional Hyperdrive-backed database URL.
- `QUEUE_PROVIDER`: `redis` for local/heavy worker deployments, `cloudflare` for Cloudflare Queue publishing.
- `REDIS_URL`: Redis connection URL.
- `REDIS_QUEUE`: Redis list name used for extraction jobs.
- `WEBHOOK_DELIVERY_QUEUE`: Queue name for webhook delivery IDs.
- `STORAGE_PROVIDER`: `minio` locally or `r2` in production.
- `S3_ENDPOINT`: S3-compatible storage endpoint. Use MinIO locally.
- `S3_ACCESS_KEY`: S3 access key.
- `S3_SECRET_KEY`: S3 secret key.
- `S3_BUCKET`: Bucket for uploaded source files.
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`: Local MinIO configuration.
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT`, `R2_PUBLIC_BASE_URL`: Cloudflare R2 configuration.
- `API_BASE_URL`: API origin used by the Next.js frontend or Cloudflare Worker gateway.
- `NEXT_PUBLIC_APP_URL`: Browser-visible app URL.
- `NEXT_PUBLIC_API_BASE_URL`: Browser-visible API URL.
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`: Browser-safe Stripe publishable key.
- `NEXT_PUBLIC_TURNSTILE_SITE_KEY`: Browser-safe Cloudflare Turnstile site key for the registration form.
- `NEXT_PUBLIC_CHEMVAULT_USER_URL`: Browser-visible ChemVault User Center URL used by `/login` and `/register` redirects.
- `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`: Cloudflare deployment/configuration values.
- `CLOUDFLARE_QUEUE_NAME`, `CLOUDFLARE_QUEUE_ID`: Optional Cloudflare Queue configuration.
- `INTERNAL_WORKER_TOKEN`: Shared secret used by Cloudflare internal workers to call protected backend endpoints.
- `ENABLE_API_DOCS`: Enables FastAPI `/docs`, `/redoc`, and `/openapi.json` when `true`.
- `WORKER_STEP_DELAY_SECONDS`: Optional local delay between worker status transitions.
- `JWT_SECRET`: Required to sign JWT access tokens.
- `JWT_EXPIRES_IN_MINUTES`: JWT lifetime in minutes. Defaults to `10080`.
- `APP_ENCRYPTION_KEY`: Required to save or read user-provided OpenAI API keys.
- `ALLOW_USER_OPENAI_KEYS`: Enables encrypted user key storage. Defaults to `true`.
- `TURNSTILE_SECRET_KEY`: Server-side Cloudflare Turnstile secret key used by `/auth/register`.
- `TURNSTILE_REQUIRED`: Set to `true` in production to require Turnstile verification for registration.
- `TURNSTILE_TIMEOUT_SECONDS`: Timeout for Turnstile server-side validation. Defaults to `5.0`.
- `CHEMVAULT_USER_BASE_URL`: Server-side ChemVault User Center origin used to validate shared sessions.
- `CHEMVAULT_USER_COOKIE_NAME`: Shared User Center cookie name. Defaults to `chemvault_session`.
- `CHEMVAULT_USER_COOKIE_DOMAIN`: Cookie domain used when clearing shared sessions from the web app. Production uses `.chemvault.science`.
- `CHEMVAULT_USER_SERVICE_KEY`: User Center service key for Extract access checks. Defaults to `chemvault_extract`.
- `CHEMVAULT_USER_REQUIRE_SERVICE_ACCESS`: Set to `true` to enforce User Center service access before syncing a user.
- `AI_PROVIDER`: AI provider. Use `openai` for the MVP.
- `OPENAI_API_KEY`: Platform OpenAI key used when a user does not use their own key.
- `OPENAI_MODEL`: Default extraction model. Defaults to `gpt-5.4`.
- `OPENAI_FALLBACK_MODEL`: Optional fallback model. Defaults to `gpt-5.5`.
- `AI_MAX_CHUNKS_PER_DOCUMENT`: Maximum selected chunks sent to OpenAI per document. Defaults to `20`.
- `AI_MAX_CHUNK_CHARS`: Maximum characters per selected chunk. Defaults to `6000`.
- `AI_ENABLE_FALLBACK_MODEL`: Set to `true` to enable fallback retry. Defaults to `false`.
- `AI_ESTIMATED_INPUT_TOKEN_RATIO`: Character-to-token estimate ratio. Defaults to `0.25`.
- `AI_MONTHLY_FREE_FILE_LIMIT`: Legacy global limit value retained for compatibility.
- `DEFAULT_FREE_MONTHLY_AI_FILE_LIMIT`: Default per-user monthly AI extraction file limit. Defaults to `10`.
- `DEFAULT_FREE_MONTHLY_AI_COST_LIMIT_USD`: Default per-user monthly AI cost limit. Defaults to `5.00`.
- `STRIPE_SECRET_KEY`: Server-side Stripe secret key. Never expose this to the frontend.
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret from `stripe listen` or the Stripe Dashboard.
- `STRIPE_CUSTOMER_PORTAL_RETURN_URL`: URL Stripe Customer Portal returns to after billing management.
- `STRIPE_CHECKOUT_SUCCESS_URL`: URL Stripe Checkout returns to after successful checkout.
- `STRIPE_CHECKOUT_CANCEL_URL`: URL Stripe Checkout returns to when cancelled.
- `STRIPE_PRICE_STUDENT_MONTHLY`: Stripe recurring monthly Price ID for Student.
- `STRIPE_PRICE_RESEARCHER_MONTHLY`: Stripe recurring monthly Price ID for Researcher.
- `STRIPE_PRICE_LAB_MONTHLY`: Stripe recurring monthly Price ID for Lab.
- `STRIPE_PRICE_STUDENT_YEARLY`: Stripe recurring yearly Price ID for Student.
- `STRIPE_PRICE_RESEARCHER_YEARLY`: Stripe recurring yearly Price ID for Researcher.
- `STRIPE_PRICE_LAB_YEARLY`: Stripe recurring yearly Price ID for Lab.
- `PUBCHEM_BASE_URL`: Optional PubChem base URL (default: `https://pubchem.ncbi.nlm.nih.gov`).
- `PUBCHEM_TIMEOUT_SECONDS`: Timeout for PubChem requests (default: `5`).
- `PUBCHEM_CACHE_TTL_SECONDS`: Cache TTL for PubChem lookups in seconds (default: `3600`).

RDKit is optional and auto-detected at runtime:
- install when available: `pip install rdkit-pypi` (or `rdkit` in your environment)
- if missing, extraction still succeeds and warnings include `rdkit_available=false`.

## Cloudflare Deployment

ChemVault Extract uses Cloudflare for edge hosting, routing, R2 object storage, optional Queue delivery, and domain/SSL. Heavy services stay outside Cloudflare Workers:

- `apps/web`: Next.js App Router deployed to Cloudflare with OpenNext as Worker `chemvault-extract-web`.
- `workers/api-gateway`: lightweight Worker at `api.chemvault.science/*` that proxies to the external FastAPI backend.
- `workers/webhook-delivery`: optional Cloudflare Queue consumer for webhook delivery orchestration.
- `services/api`: FastAPI, PostgreSQL access, parsing, Docling/PDF work, OpenAI extraction, RDKit/PubChem, and long-running jobs. Deploy this to Railway, Render, Fly.io, a VPS, or another Docker host.
- PostgreSQL remains PostgreSQL. Do not migrate this app to D1; the schema and future pgvector/search needs require a PostgreSQL provider such as Neon, Supabase, Railway PostgreSQL, or managed Postgres with pgvector support.

Recommended production domains:

- `app.chemvault.science` -> Cloudflare frontend Worker.
- `api.chemvault.science` -> API gateway Worker or external backend.
- `files.chemvault.science` -> optional R2 public/custom domain.
- `docs.chemvault.science` -> optional future docs site.

### Frontend

The frontend config lives in `apps/web/wrangler.jsonc`.

Manual deployment:

```bash
npm ci
npm run deploy:web
```

Cloudflare Dashboard setup:

1. Open Cloudflare Dashboard.
2. Go to Workers & Pages.
3. Create or connect a project from the GitHub repository.
4. Use `apps/web` as the app directory if using Git integration.
5. Build command: `npm ci && npm run cf:build -w apps/web`.
6. Deploy command for Worker mode: `npm run cf:deploy -w apps/web`.
7. Configure environment variables:
   - `API_BASE_URL=https://api.chemvault.science`
   - `NEXT_PUBLIC_API_BASE_URL=https://api.chemvault.science`
   - `NEXT_PUBLIC_APP_URL=https://app.chemvault.science`
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=...`
8. Bind custom domain `app.chemvault.science`.
9. Test `https://app.chemvault.science/health`.

This app is not configured as a static `output: "export"` site because it uses App Router server routes and authenticated proxy handlers.

### API Gateway Worker

Config: `workers/api-gateway/wrangler.jsonc`.

The gateway:

- returns `GET /health` as `{ "status": "ok", "service": "cloudflare-api-gateway" }`;
- forwards Authorization and API key headers;
- forwards multipart uploads without parsing the body;
- preserves Stripe/webhook raw bodies by streaming the original request body;
- strips `/api` only when requests arrive as `/api/*`;
- adds `x-request-id`;
- restricts CORS to `ALLOWED_ORIGINS`.

Deploy:

```bash
npm run deploy:api-gateway
```

Set `BACKEND_API_URL` in `workers/api-gateway/wrangler.jsonc` or the Cloudflare Dashboard environment variables to the external FastAPI origin, for example a Railway/Fly/Render URL. Bind custom domain `api.chemvault.science` to the Worker in Cloudflare.

### R2 Storage

Production storage uses R2 through the existing S3-compatible storage interface.

1. Create an R2 bucket, for example `chemvault-documents`.
2. Create R2 access keys.
3. Configure the backend environment:

```bash
STORAGE_PROVIDER=r2
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=chemvault-documents
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_PUBLIC_BASE_URL=
```

Local development still uses MinIO:

```bash
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=chemvault
MINIO_SECRET_KEY=chemvault-secret
MINIO_BUCKET=chemvault-documents
```

Uploaded documents, parsed assets, and export files should use the storage interface rather than storing file contents in PostgreSQL.

### Queue Strategy

Local and heavy production workers default to Redis:

```bash
QUEUE_PROVIDER=redis
REDIS_URL=redis://...
REDIS_QUEUE=chemvault:extract:jobs
WEBHOOK_DELIVERY_QUEUE=chemvault:webhook:deliveries
```

Cloudflare Queues are optional. Use them for lightweight webhook delivery or future edge jobs, not for Python PDF parsing, Docling, RDKit, or long-running OpenAI extraction unless you split those jobs into Worker-safe consumers.

```bash
QUEUE_PROVIDER=cloudflare
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_QUEUE_NAME=chemvault-webhook-delivery
CLOUDFLARE_QUEUE_ID=...
```

The Python worker cannot consume Cloudflare Queues directly; deploy a Queue consumer Worker or keep Redis for the heavy worker.

### Webhook Delivery Worker

Config: `workers/webhook-delivery/wrangler.jsonc`.

This Worker consumes `chemvault-webhook-delivery` queue messages containing delivery IDs. It calls internal backend endpoints to prepare a signed webhook request, sends the HTTP POST, then reports status back to the backend. The backend stores retry state and response previews.

Required secret:

```bash
wrangler secret put INTERNAL_WORKER_TOKEN --config workers/webhook-delivery/wrangler.jsonc
```

The same `INTERNAL_WORKER_TOKEN` must be configured on the FastAPI backend. Do not log it.

### PostgreSQL and Hyperdrive

Keep PostgreSQL as the source database. Recommended providers are Neon, Supabase, Railway PostgreSQL, Fly Postgres, or another managed PostgreSQL service.

Use Cloudflare Hyperdrive only if a Worker needs direct database access:

```bash
HYPERDRIVE_BINDING=
HYPERDRIVE_DATABASE_URL=
```

The current API gateway proxies to FastAPI and does not need direct database access.

### GitHub Actions

`.github/workflows/deploy-cloudflare.yml` deploys the frontend Worker, API gateway Worker, and webhook delivery Worker on pushes to `main`.

Required GitHub secrets:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` if Stripe checkout is public in production

Backend deployment is intentionally a placeholder in this workflow. Deploy `services/api` and the Python worker separately on your Docker backend.

### Cloudflare Secrets

Do not commit real secrets. Use Wrangler:

```bash
wrangler secret put INTERNAL_WORKER_TOKEN --config workers/webhook-delivery/wrangler.jsonc
```

For the frontend Worker, configure runtime/build variables in Cloudflare or GitHub Actions. `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is safe for the browser. Never expose `TURNSTILE_SECRET_KEY`, `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, `R2_SECRET_ACCESS_KEY`, `APP_ENCRYPTION_KEY`, or `JWT_SECRET` to the browser.

### Optional Cloudflare Access

To protect staging:

1. Create an Access application for `staging.chemvault.science`.
2. Allow selected email addresses or identity groups.
3. Leave the public landing page unprotected unless intentionally running a private beta.

### Production Safety Checklist

- Do not commit `.env` or real keys.
- Set `CORS_ALLOWED_ORIGINS=https://app.chemvault.science` in production.
- Keep `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, R2 secrets, JWT secrets, and encryption keys only in backend/Cloudflare secret stores.
- Preserve raw request bodies for `/webhooks/stripe` and webhook proxy paths.
- Keep multipart upload proxying streaming through the API gateway.
- Do not point preview deployments at the production database unless explicitly intended.
- Test:
  - `https://app.chemvault.science/health`
  - `https://api.chemvault.science/health`
  - FastAPI `/health`
  - upload to R2
  - export storage key creation
  - Stripe webhook delivery to backend

## License

This repository is source-available but not open source. Public visibility is
for review and reference only; no rights are granted to use, copy, modify,
distribute, host, deploy, or create derivative works without prior written
permission from Ziwen Mu or the repository owner.

See [LICENSE](./LICENSE). All rights reserved.
