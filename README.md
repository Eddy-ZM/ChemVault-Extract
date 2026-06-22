# ChemVault Extract

Production-ready MVP foundation for ingesting chemistry papers, lab reports, and instrument-exported files into an AI Scientific Data Extraction / Research Intelligence pipeline.

This project does not implement AI extraction yet and does not call the OpenAI API. It includes the monorepo, Next.js frontend, FastAPI backend, PostgreSQL models, MinIO file storage, Redis job queue, and a Python worker skeleton that advances queued jobs through the first-stage pipeline.

## Services

- `web`: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui-style components
- `api`: FastAPI service with upload, document, job, and health endpoints
- `worker`: Python Redis worker, packaged from `services/worker`, that reserves the future parsing/extraction boundary and currently moves jobs through `parsing` to `review_ready`
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

Open:

- Frontend: [http://localhost:3000](http://localhost:3000)
- API health: [http://localhost:8000/health](http://localhost:8000/health)
- MinIO console: [http://localhost:9001](http://localhost:9001)

Default MinIO credentials are `chemvault` / `chemvault-secret`.

## Test Upload

1. Open [http://localhost:3000/documents/upload](http://localhost:3000/documents/upload).
2. Upload a supported file: PDF, DOCX, CSV, XLSX, TXT, or MD.
3. The upload page shows the created document ID and extraction job ID.
4. Open the document detail page to watch the worker update the job status.
5. Open `/documents/{document_id}/review` to see the placeholder review workspace.
6. Confirm the object exists in MinIO under the `chemvault-documents` bucket.

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
- `GET /documents/{document_id}/pages`
- `GET /documents/{document_id}/blocks`
- `GET /documents/{document_id}/chunks`
- `GET /jobs/{job_id}`

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

The first-stage worker intentionally does not perform real parsing or AI extraction. For now, it:

1. Pops queued job IDs from Redis.
2. Updates the job to `parsing`.
3. Updates the job to `review_ready`.
4. Marks failures as `failed`.

Parser modules are kept in `services/api/app/parsers` as the next integration point for Docling, GROBID, RDKit, LLM structured outputs, and PubChem enrichment. These modules are not used by the current worker to create extraction records.

Planned parser inputs:

- PDF: attempts Docling if installed, then falls back to `pypdf`
- DOCX: extracts headings and paragraphs with `python-docx`
- CSV: creates a table block and text representation
- XLSX: parses each sheet as a table block
- TXT / MD: extracts headings and paragraphs

Scientific section detection recognizes common sections such as Abstract, Introduction, Experimental, Materials and Methods, Results, Discussion, Supporting Information, References, and Appendix. References will be excluded from chunks by default once parsing is enabled in the worker.

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
