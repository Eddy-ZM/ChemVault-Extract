# Verification Map

## Existing coverage

| Use case | Rule/negative case | Evidence | Status |
| --- | --- | --- | --- |
| Browser/API cutover | Product routes redirect to fixed Lab successor; `/api/*` returns structured 410; static/health paths remain local | middleware; frontend build; local runtime smoke | CI required |
| SDK retirement | JavaScript/Python clients reject construction without an explicit self-hosted base URL | SDK unit tests | CI required |
| Token-bounded chunks | CJK, SMILES, formulas, and prose remain under the conservative budget; invalid budget fails | parser tests and `chunking.py` | API test suite |
| Lifecycle | Service-authenticated export/delete is owner-scoped and idempotent | `test_lifecycle.py` | API test suite |
| Legacy security/reliability | Auth, tenant scope, parsers, normalization, exports, billing and webhooks | existing API/web suites | CI required while code is retained |

## Proposed tests

| Test | Type | Expected behavior |
| --- | --- | --- |
| Deployed redirect smoke | Guarded live | `/`, `/dashboard`, and a document route redirect to Lab; `/api/projects` returns 410; `/health` remains local |
| Historical export/delete canary | Guarded live | Representative legacy owner reaches terminal export/delete state |
| API/SDK traffic census | Operational | Logs quantify remaining consumers before endpoint retirement |

## Gaps

- No local test can prove historical production data was migrated, exported, or deleted.
- The redirect deployment intentionally does not prove the frozen FastAPI/Redis/PostgreSQL stack is healthy.
- Final domain/worker removal still requires deployed traffic and retention evidence outside the repository; local smoke already proves 307/410/200 behavior against the production build.
