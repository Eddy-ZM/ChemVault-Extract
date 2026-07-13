# Automation

| Automation | Trigger/owner | Allowed calls and inputs | Guardrails/failure |
| --- | --- | --- | --- |
| Sunset redirect | Browser request; Extract edge owner | Fixed Lab origin only; preserves path/query | API/static exclusions, no user-chosen host, deprecation headers |
| Legacy extraction jobs | Existing authenticated API request; maintenance only | Frozen parser/provider/object-store/queue surface | Owner/workspace auth, quotas, bounded chunks, provider schemas; no net-new features |
| Webhook delivery | Existing billing/project event | Registered endpoint/provider only | Signature, retry state, endpoint ownership, audit record |
| Lifecycle reconciliation | User Center service | Legacy owner export/delete endpoints only | Dedicated credential, idempotency, terminal status |

The public deployment no longer creates queues or deploys backend workers. Re-enabling legacy automation requires an explicit rollback decision and a verified backend; it must never occur because a secret happened to be present.
