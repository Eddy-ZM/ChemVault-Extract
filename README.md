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
6. Click `Estimate cost` to preview selected chunks, model, and estimated OpenAI cost.
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
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /documents/upload`
- `POST /documents/{document_id}/extract`
- `POST /documents/{document_id}/extract-ai`
- `GET /documents/{document_id}/pages`
- `GET /documents/{document_id}/blocks`
- `GET /documents/{document_id}/tables`
- `GET /documents/{document_id}/chunks`
- `GET /documents/{document_id}/extractions`
- `GET /documents/{document_id}/review-items`
- `GET /jobs/{job_id}`
- `PATCH /review-items/{review_item_id}`

## Database Foundation

Core tables:

- `projects`
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

## Parsing Pipeline

The first-stage worker performs document parsing only. It does not perform AI extraction, reaction extraction, RDKit processing, PubChem enrichment, or OpenAI API calls.

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

The extraction layer uses `AI_PROVIDER=openai` by default. It sends only selected `DocumentChunk` text to OpenAI, never the original PDF or full uploaded object. If `OPENAI_API_KEY` is missing, `POST /documents/{document_id}/extract-ai` returns `OPENAI_API_KEY is missing. Please configure it before running AI extraction.`

OpenAI API usage is metered. Use `POST /documents/{document_id}/estimate-ai-cost` or the `Estimate cost` button before running extraction.

Configure API access in `.env`:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
AI_ENABLE_FALLBACK_MODEL=false
```

When the user clicks `Run AI Extraction`, the API creates an `ai_extraction` job. The worker:

1. Uses existing chunks when the document is already parsed.
2. Parses first if no chunks exist.
3. Selects at most `AI_MAX_CHUNKS_PER_DOCUMENT` chunks by section priority.
4. Truncates each selected chunk to `AI_MAX_CHUNK_CHARS`.
5. Moves the job through `extracting`, `validating`, and `review_ready`.
6. Runs the four extractor interfaces:
   - `metadata`
   - `chemical_entities`
   - `reactions`
   - `measurements`
7. Saves one `ExtractionRun` per extractor with provider, model, selected chunk IDs, estimated tokens, estimated cost, raw output, and parsed output.

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
- `gpt-5.5`: input `$5.00 / 1M`, output `$30.00 / 1M`

The extractor modules live in `services/api/app/extractors`:

- `schemas.py`: JSON-schema-ready Pydantic models for metadata, chemical entities, reactions, measurements, and evidence.
- `prompts.py`: the system prompt for strict source-grounded extraction.
- `base.py`: extractor interface and chunk selection.
- `metadata_extractor.py`, `chemical_extractor.py`, `reaction_extractor.py`, `measurement_extractor.py`: extractor-specific section targeting.
- `openai_client.py`: OpenAI Responses API structured-output client.
- `pipeline.py`: orchestrates OpenAI calls, schema validation, fallback handling, record persistence, and review item creation.

The validation modules live in `services/api/app/validators`:

- `evidence_validator.py`: checks `document_id`, `chunk_id`, page range, and whether `quote` appears in the chunk text.
- `chemistry_validator.py`: placeholder normalization checks for confidence and measurement type.

Review UI is available at `/documents/{document_id}/review`. It can list review items, approve, reject, and edit `extractedData`. AI output is schema-validated before records are written, and evidence quotes are checked against the source chunk before review status is assigned.

Fallback model behavior is disabled by default. Set `AI_ENABLE_FALLBACK_MODEL=true` to retry once with `OPENAI_FALLBACK_MODEL` when the default model call or schema validation fails. Fallback attempts are recorded as `ExtractionRun` rows.

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
- `REDIS_URL`: Redis connection URL.
- `REDIS_QUEUE`: Redis list name used for extraction jobs.
- `S3_ENDPOINT`: S3-compatible storage endpoint. Use MinIO locally.
- `S3_ACCESS_KEY`: S3 access key.
- `S3_SECRET_KEY`: S3 secret key.
- `S3_BUCKET`: Bucket for uploaded source files.
- `API_BASE_URL`: API origin used by the Next.js frontend or Cloudflare Worker gateway.
- `WORKER_STEP_DELAY_SECONDS`: Optional local delay between worker status transitions.
- `AI_PROVIDER`: AI provider. Use `openai` for the MVP.
- `OPENAI_API_KEY`: Required before running AI extraction.
- `OPENAI_MODEL`: Default extraction model. Defaults to `gpt-4.1-mini`.
- `OPENAI_FALLBACK_MODEL`: Optional fallback model. Defaults to `gpt-5.5`.
- `AI_MAX_CHUNKS_PER_DOCUMENT`: Maximum selected chunks sent to OpenAI per document. Defaults to `20`.
- `AI_MAX_CHUNK_CHARS`: Maximum characters per selected chunk. Defaults to `6000`.
- `AI_ENABLE_FALLBACK_MODEL`: Set to `true` to enable fallback retry. Defaults to `false`.
- `AI_ESTIMATED_INPUT_TOKEN_RATIO`: Character-to-token estimate ratio. Defaults to `0.25`.
- `AI_MONTHLY_FREE_FILE_LIMIT`: Simple monthly successful AI extraction job limit. Defaults to `10`.

## Cloudflare Frontend Deployment

The Next.js frontend is configured for Cloudflare Workers through OpenNext.

Production target:

- Worker: `chemvault-extract-web`
- Custom domain: `app.chemvault.science`
- Zone: `chemvault.science`

GitHub automatic deployment is configured in `.github/workflows/deploy-cloudflare.yml`.
Every push to `main` that changes the frontend, shared packages, package lockfile, or the workflow builds the Next.js app with OpenNext and deploys it with Wrangler.

Required GitHub secret:

- `CLOUDFLARE_API_TOKEN`: a Cloudflare API token with permission to deploy the `chemvault-extract-web` Worker and manage its custom domain route.

Suggested token permissions:

- Account: `Workers Scripts Write`
- Zone (`chemvault.science`): `Workers Routes Write`
- Zone (`chemvault.science`): `Zone Read`

Set the secret with:

```bash
gh secret set CLOUDFLARE_API_TOKEN --repo Eddy-ZM/ChemVault-Extract
```

The Worker config lives in `apps/web/wrangler.jsonc`. It sets `API_BASE_URL=https://api.chemvault.science` for the deployed frontend; update that value when the production API endpoint changes.

Manual deployment from an authenticated machine:

```bash
npm ci
npm run cf:build -w apps/web
CLOUDFLARE_ACCOUNT_ID=20f69e8d2aebbadbff2b6ffa36efee50 \
  CLOUDFLARE_API_TOKEN=... \
  npm run cf:deploy -w apps/web
```
