# ChemVault Extract transition plan

ChemVault Extract is in maintenance mode. ChemVault Lab is the successor for new laboratory analysis workflows.

## Product rules

- Do not add net-new product features to Extract.
- Continue security, reliability, export, and data-lifecycle maintenance.
- Direct new analysis workflows to `https://lab.chemvault.science`.
- Keep existing projects, exports, and deletion requests available during migration.

## Exit gates

1. Publish a Lab migration guide and verify representative Extract exports can be imported or retained as read-only evidence.
2. Resolve or cancel active Extract subscriptions and transfer shared workspaces before individual account deletion.
3. Move Extract to read-only mode after active usage and paid subscriptions reach zero.
4. Decommission compute and storage only after export completion, deletion-job reconciliation, and the published retention window.

The lifecycle endpoint under `/internal/lifecycle/{userSystemId}` is the control-plane integration used by ChemVault User Center for export and deletion reconciliation.

Set `READ_ONLY_MODE=true` after the census and customer-communication gates are satisfied. Historical reads, data exports, billing webhooks, logout, and lifecycle deletion remain available; other writes return HTTP 410 with `Deprecation`, `Sunset`, and successor `Link` headers.

The protected `GET /internal/sunset/census` endpoint reports users, active paid subscriptions, documents, open batch jobs, and pending exports. Review it before enabling read-only mode and again before final shutdown.
