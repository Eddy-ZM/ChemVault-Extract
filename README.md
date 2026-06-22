# ChemVault Extract

Production-ready MVP foundation for ingesting chemistry papers, lab reports, and instrument-exported files into a structured extraction pipeline.

This project does not implement AI extraction yet. It includes the monorepo, Next.js frontend, FastAPI backend, PostgreSQL models, MinIO file storage, Redis job queue, and a Python worker that parses uploaded files into pages, blocks, tables, and chunks for future AI extraction.

## Services

- `web`: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui-style components
- `api`: FastAPI service with upload, document, job, and health endpoints
- `worker`: Python Redis worker that downloads files from MinIO, parses them, stores pages/blocks/chunks, and moves jobs through `parsing`, `chunking`, `review_ready`
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
5. Use the `Overview`, `Pages`, `Blocks`, and `Chunks` tabs to inspect parsed content.
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

## Parsing

Supported parser inputs:

- PDF: attempts Docling if installed, then falls back to `pypdf`
- DOCX: extracts headings and paragraphs with `python-docx`
- CSV: creates a table block and text representation
- XLSX: parses each sheet as a table block
- TXT / MD: extracts headings and paragraphs

Scientific section detection recognizes common sections such as Abstract, Introduction, Experimental, Materials and Methods, Results, Discussion, Supporting Information, References, and Appendix. References are excluded from chunks by default.

## Local Development Without Docker

Install frontend dependencies:

```bash
npm install
npm run dev
```

Install backend dependencies:

```bash
cd services/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

For non-Docker frontend development, set `API_BASE_URL=http://localhost:8000` in `.env`.
