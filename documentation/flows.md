# Critical Flows

| Flow | Actor/precondition | Sequence and side effects | Deny/failure behavior |
| --- | --- | --- | --- |
| Browser cutover | Any visitor | Middleware sends non-API product paths and query strings to `lab.chemvault.science` with deprecation and successor headers | Static and health paths remain local; successor host is configuration-owned |
| Public legacy API retirement | Any API caller | Middleware terminates `/api/*` with JSON HTTP 410, `Deprecation`, successor `Link`, and no-store headers | Request never reaches a legacy Next route or dead Extract origin; caller must move to authenticated Lab contracts |
| Legacy SDK use | Self-hosted recovery operator only | JavaScript/Python client requires an explicit legacy base URL | Missing base URL fails during client construction; there is no hosted API default |
| Legacy data export | Existing authenticated Extract user | Owner/workspace checks load records and generate export artifacts | Cross-tenant IDs are denied; missing backend means export is unavailable and must not be claimed complete |
| Lifecycle reconciliation | User Center service | Protected endpoint inventories, exports, or deletes legacy owner data idempotently | Missing/mismatched service credential fails closed |
| Read-only transition | Operator after census/communication gates | `READ_ONLY_MODE` rejects writes while reads, exports, logout, billing webhooks, and lifecycle remain | Write returns 410 with deprecation metadata; do not enable before export gates |
| Lab compatibility | Legacy client moved to Lab | Lab maps supported document/job/search/export contracts onto Lab records | Unsupported behavior is explicit; no fallback to the dead API origin |

Final shutdown requires zero active paid subscriptions/open jobs, reconciled exports/deletions, API/SDK traffic below the agreed threshold, and a published retention window.
