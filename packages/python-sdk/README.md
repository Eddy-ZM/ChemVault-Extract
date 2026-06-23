# ChemVault Python SDK

Python SDK for the ChemVault Extract `/v1` developer API.

Package publishing is not enabled yet. Use local package installation during development:

```bash
pip install -e packages/python-sdk
```

```python
from chemvault import ChemVault, ChemVaultError

client = ChemVault(api_key="cv_live_xxx")

project = client.projects.create(name="Organic synthesis")
document = client.documents.upload(
    project_id=project.id,
    file_path="paper.pdf",
)

estimate = client.documents.estimate(document.id)
job = client.documents.extract(document.id)
records = client.documents.records(document.id)
```

Custom base URL:

```python
client = ChemVault(
    api_key="cv_test_xxx",
    base_url="http://localhost:8000",
    timeout=20,
)
```

Errors:

```python
try:
    client.projects.list()
except ChemVaultError as exc:
    print(exc.code, exc.status_code, exc.request_id, exc.details)
```

The SDK uses API key authentication and does not bypass plan limits, API scopes, rate limits, evidence validation, or review workflow behavior.
