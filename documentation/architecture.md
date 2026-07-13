# Architecture

## Product state

ChemVault Extract is a sunset compatibility repository. ChemVault Lab owns all new laboratory extraction, review, search, batch, and export journeys. The Next.js/OpenNext surface at `app.chemvault.science` redirects non-API routes to the equivalent Lab path and publishes deprecation/successor headers. Public `/api/*` traffic is terminated at middleware with structured HTTP 410, while `/health` remains available for deployment checks.

The legacy FastAPI/PostgreSQL/Redis/R2 implementation remains source evidence for export, lifecycle, and compatibility work; its backend and queue workers are no longer deployed by the public frontend workflow.

## Trust boundaries

- Browser product traffic terminates at the fixed Lab successor URL; request parameters cannot choose another redirect host.
- Public legacy API traffic cannot bypass retirement middleware into old Next handlers, and SDKs cannot silently select a dead hosted origin.
- Legacy API code derives user/workspace scope server-side and keeps lifecycle operations behind a service credential.
- Provider, Stripe, database, object-store, email, webhook, and queue secrets remain server-side.
- Lab compatibility APIs operate on Lab-owned records and are not evidence that historical Extract records were migrated.

## Known risks/assumptions

- Historical customer data requires an explicit census, export, retention, and deletion decision before infrastructure removal.
- API/SDK consumers do not follow browser redirects; compatibility retirement requires traffic evidence and communication.
- `PRODUCT_MODE=legacy` is an emergency rollback only and must not be enabled without a healthy legacy backend.

There is no scheduled job owned here. Legacy AI, webhooks, lifecycle, and queue behavior is documented in `automation.md`.

## Related documents

- [Flows](flows.md)
- [Permissions](permissions.md)
- [Variables](variables.md)
- [Tests](tests.md)
- [Automation](automation.md)
- [Sunset plan](../SUNSET_PLAN.md)
