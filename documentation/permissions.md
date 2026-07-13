# Permissions

| Resource/operation | Public | Authenticated owner | Workspace member | Admin/operator | User lifecycle service |
| --- | --- | --- | --- | --- | --- |
| Product pages | Redirect to Lab | Redirect to Lab | Redirect to Lab | Redirect to Lab | N/A |
| Public `/api/*` | HTTP 410 only | HTTP 410 only | HTTP 410 only | HTTP 410 only | N/A |
| Legacy projects/documents/records | Deny | Own scope | Granted workspace scope | Audited support scope | Export/delete only |
| Legacy export | Deny | Own scope | Granted workspace scope | Audited support scope | Reconciliation scope |
| Billing portal/subscription | Deny | Own account | Deny | Provider console | Reconciliation only |
| Sunset census/read-only control | Deny | Deny | Deny | Internal service credential | Deny |
| Lifecycle export/delete | Deny | Through User Center | Deny | Audited operator | Internal credential |

PostgreSQL does not supply application RLS; every query must include the server-derived user or accessible-workspace set. Browser UI checks are not authorization. Lab owns new records and has its own owner-scope enforcement.
