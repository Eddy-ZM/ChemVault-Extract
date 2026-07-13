# Extract data-retirement evidence

Verified on 2026-07-12 against the GitHub repository `Eddy-ZM/ChemVault-Extract`, the authenticated Cloudflare account used by the ChemVault suite, public DNS, and the local runtime configuration.

## Findings

| Surface | Result |
| --- | --- |
| Public legacy API | `api.chemvault.science` has no DNS record |
| Cloudflare Pages | No Extract project is present; Lab is the canonical successor |
| Cloudflare D1 | No Extract-named database is present |
| Cloudflare R2 | No Extract-named bucket is present |
| Cloudflare Queues | The authenticated OAuth inventory returned no queues |
| GitHub Actions secrets | Only Cloudflare deployment credentials and the lifecycle service secret are present |
| GitHub Actions variables/environments | No production data-plane variables or environments are present |
| Local database/cache/storage | Configured endpoints resolve to localhost only |
| Billing | No local Stripe secret and no GitHub Stripe secret/variable are configured |

The inventory found no production Extract dataset or managed runtime resource to transfer or destroy. No destructive command was run.

## Repeatable checks

Run the following with the suite's authenticated operator accounts. Never print secret values.

```powershell
gh secret list --repo Eddy-ZM/ChemVault-Extract
gh variable list --repo Eddy-ZM/ChemVault-Extract
npx wrangler pages project list
npx wrangler d1 list
npx wrangler r2 bucket list
Remove-Item Env:CLOUDFLARE_API_TOKEN -ErrorAction SilentlyContinue
npx wrangler queues list
Resolve-DnsName api.chemvault.science -ErrorAction SilentlyContinue
```

## Late-discovery rule

If another account, host, database, object store, billing account, or backup containing Extract data is discovered, stop retirement work. Use the protected lifecycle census and export endpoints, reconcile shared workspaces and subscriptions, retain a checksum-protected export, and only then approve deletion. The absence recorded here applies to the verified operational scope and is not permission to delete an unverified external resource.
