# ChemVault Extract

ChemVault Extract is the retired predecessor of ChemVault Lab. It is retained during the migration window for compatibility, security maintenance, historical export, billing reconciliation, and account-lifecycle work.

All new laboratory workflows now belong to [ChemVault Lab](https://lab.chemvault.science):

- laboratory document and instrument-file upload;
- deterministic and AI-assisted structured extraction;
- document, chemical, reaction, and measurement records;
- review, correction, approval, search, batch processing, and exports;
- Files import, derived-artifact writeback, and notification events;
- Extract-compatible API routes backed by Lab-owned records.

The public Extract website redirects product routes to the equivalent Lab location. Requests under `/api/*` return a structured HTTP 410 response naming Lab as the successor; they are not proxied to the frozen backend. The published JavaScript and Python clients also require an explicit self-hosted legacy base URL and no longer default to a hosted Extract API. The deployment workflow publishes only this sunset surface; it no longer deploys the legacy FastAPI gateway, webhook queue, or background workers.

Historical Extract data is not assumed to be migrated merely because compatible Lab routes exist. Legacy infrastructure may be removed only after the census, export/deletion reconciliation, subscription closure, retention, traffic, and customer-communication gates in [SUNSET_PLAN.md](SUNSET_PLAN.md) are complete.

No net-new product features should be added here. See [documentation/architecture.md](documentation/architecture.md) for the maintained trust boundaries and verification map.
