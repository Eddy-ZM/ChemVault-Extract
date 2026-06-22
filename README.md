# ChemVault Extract

Production-ready MVP foundation for ingesting chemistry papers, lab reports, and instrument-exported files into an AI Scientific Data Extraction / Research Intelligence pipeline.

This project does not call the OpenAI API by default. It includes the monorepo, Next.js frontend, FastAPI backend, PostgreSQL models, MinIO file storage, Redis job queue, a Python parsing worker, and an offline structured-extraction pipeline foundation.

## Services

- `web`: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui-style components
- `api`: FastAPI service with upload, document, job, and health endpoints
- `worker`: Python Redis worker, packaged from `services/worker`, that parses uploaded files into pages, blocks, table blocks, and chunks, then can run an offline structured-extraction pipeline foundation
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
6. Click `Run AI Extraction` to run the structured extraction pipeline. In default offline mode this records skipped extractor runs and does not create fake records.
7. Open `/documents/{document_id}/review` to inspect review items once a real extraction provider is connected.
8. Confirm the object exists in MinIO under the `chemvault-documents` bucket.

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

The extraction layer is wired end to end but defaults to `AI_EXTRACTION_PROVIDER=none`. In this mode it does not call OpenAI or any external LLM, does not generate records, and does not create fake chemistry data.

When the user clicks `Run AI Extraction`, the API creates an `ai_extraction` job. The worker:

1. Uses existing chunks when the document is already parsed.
2. Parses first if no chunks exist.
3. Moves the job through `extracting`, `validating`, and `review_ready`.
4. Runs the four extractor interfaces in offline mode:
   - `metadata`
   - `chemical_entities`
   - `reactions`
   - `measurements`
5. Saves one skipped `ExtractionRun` per extractor with selected chunk IDs and empty parsed output.

The extractor modules live in `services/api/app/extractors`:

- `schemas.py`: JSON-schema-ready Pydantic models for metadata, chemical entities, reactions, measurements, and evidence.
- `prompts.py`: the future system prompt for strict source-grounded extraction.
- `base.py`: extractor interface and chunk selection.
- `metadata_extractor.py`, `chemical_extractor.py`, `reaction_extractor.py`, `measurement_extractor.py`: extractor-specific section targeting.
- `pipeline.py`: orchestrates the current offline provider.

The validation modules live in `services/api/app/validators`:

- `evidence_validator.py`: checks `document_id`, `chunk_id`, page range, and whether `quote` appears in the chunk text.
- `chemistry_validator.py`: placeholder normalization checks for confidence and measurement type.

Review UI is available at `/documents/{document_id}/review`. It can list review items, approve, reject, and edit `extractedData`. In offline mode the list is normally empty; real review items will appear when an extraction provider is connected and returns evidence-backed records.

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
- `AI_EXTRACTION_PROVIDER`: `none` by default. Future values can enable a real LLM provider.
- `AI_MODEL`: model/provider label stored on extraction runs. Defaults to `offline-no-provider`.

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
