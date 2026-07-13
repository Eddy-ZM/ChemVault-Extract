# Runtime Variables

| Name/group | Used by | Scope/source | Rotation | Failure/risk |
| --- | --- | --- | --- | --- |
| `NEXT_PUBLIC_CHEMVAULT_LAB_URL`, `NEXT_PUBLIC_PRODUCT_MODE` | Sunset redirect and API 410 successor metadata | Build/runtime public config | On successor/cutover decision | Wrong value misroutes users; URL is operator-controlled |
| `DATABASE_URL`, Redis/queue settings | Legacy API/jobs | Server secrets/variables | Resource migration | Legacy data/job paths unavailable |
| Object-store credentials | Legacy documents/exports | Server secrets | Every 90 days/incident | Reads/exports unavailable; never expose client-side |
| AI/provider keys | Legacy extraction | Server secrets | Provider policy/incident | Extraction unavailable; frozen feature surface |
| Stripe secrets/webhook secret | Existing subscriptions | Server secrets | Provider policy/incident | Billing reconciliation unavailable |
| `LIFECYCLE_SERVICE_SECRET` | User export/delete | Shared server secret | Every 90 days/incident | Lifecycle calls denied |
| `READ_ONLY_MODE` | Legacy write gate | Server variable | Cutover decision | Enabling too early blocks migrations; disabling reopens writes |
| Cloudflare deploy credentials | Redirect surface only | GitHub secrets | Every 90 days/incident | Redirect deployment fails |

No SDK environment variable supplies a default hosted Extract API; a self-hosted recovery client must receive its base URL explicitly. No private secret may use a `NEXT_PUBLIC_` prefix. Before any legacy activation, validate the backend health, database/Redis/object storage, service credentials, billing webhooks, census, and rollback owner. Normal production requires only the Lab URL/product mode and Cloudflare deploy credentials for the redirect surface.
