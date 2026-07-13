# ChemVault Extract transition plan

ChemVault Extract is in maintenance mode. ChemVault Lab is the successor for new laboratory analysis workflows.

## Product rules

- Do not add net-new product features to Extract.
- Continue security, reliability, export, and data-lifecycle maintenance.
- Direct new analysis workflows to `https://lab.chemvault.science`.
- Keep the frozen export/lifecycle implementation available only as a recovery path if an independently managed legacy data plane is discovered.
- Publish only the browser redirect surface from this repository; do not recreate the legacy API gateway or queues as part of normal Extract deployment.

## Exit gates

1. Publish a Lab migration guide and verify representative Extract exports can be imported or retained as read-only evidence.
2. Resolve or cancel active Extract subscriptions and transfer shared workspaces before individual account deletion.
3. Move Extract to read-only mode after active usage and paid subscriptions reach zero.
4. Decommission compute and storage only after export completion, deletion-job reconciliation, and the published retention window.
5. Confirm API/SDK traffic is below the approved retirement threshold and every public product entry point names Lab as the authority.

## Gate disposition (2026-07-12)

- Successor coverage is complete: Lab owns the former Extract product journeys and exposes owner-scoped compatibility routes.
- The public redirect is ready for the next Git-backed Pages deployment; the legacy API, queues, and workers are absent from the deployment workflow.
- The active Cloudflare account contains no Extract-named Pages project, D1 database, R2 bucket, or Queue. `api.chemvault.science` has no DNS record.
- The Extract GitHub repository contains no production database, Redis, object-storage, or Stripe secret/variable. Its local data-plane configuration points only to localhost and has no Stripe secret.
- Therefore there is no discovered production Extract dataset, active paid data plane, or managed compute/storage resource to migrate or delete. The lifecycle export/delete implementation remains frozen as a recovery path if a separately managed legacy environment is discovered later.
- The evidence and repeatable inventory commands are recorded in `documentation/data-retirement-evidence.md`; the Lab-side late-discovery procedure is recorded in `ChemVault-Lab/documentation/extract-migration.md`.

## Current cutover state

- Non-API browser routes redirect to the equivalent ChemVault Lab path with deprecation and successor headers.
- Public `/api/*` requests return structured HTTP 410 with successor metadata; the SDKs have no default hosted Extract origin.
- ChemVault Lab owns new upload, analysis, records, review, batch, search, export, Files writeback, and event workflows.
- The Extract deployment workflow no longer deploys the legacy FastAPI gateway, webhook queue, or background workers.
- No historical production data plane was discovered in the verified Cloudflare/GitHub scope. Do not claim that an independently managed dataset was migrated; if one is discovered, apply the documented late-discovery procedure before deletion.

The frozen lifecycle endpoint under `/internal/lifecycle/{userSystemId}` is the recovery control-plane implementation for export and deletion reconciliation. It is not exposed by the public redirect deployment.

Set `READ_ONLY_MODE=true` after the census and customer-communication gates are satisfied. Historical reads, data exports, billing webhooks, logout, and lifecycle deletion remain available; other writes return HTTP 410 with `Deprecation`, `Sunset`, and successor `Link` headers.

The protected `GET /internal/sunset/census` endpoint reports users, active paid subscriptions, documents, open batch jobs, and pending exports. Review it before enabling read-only mode and again before final shutdown.
