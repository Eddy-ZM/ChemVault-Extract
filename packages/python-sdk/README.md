# ChemVault Extract Python SDK (retired)

The hosted ChemVault Extract `/v1` API has been retired. Current product workflows live in [ChemVault Lab](https://lab.chemvault.science).

Package publishing is not enabled yet. Use local package installation during development:

```bash
pip install -e packages/python-sdk
```

```python
from chemvault import ChemVault, ChemVaultError

client = ChemVault(
    api_key="legacy-self-hosted-key",
    base_url="http://localhost:8000",
)

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

There is intentionally no hosted default base URL. Use this package only for an explicitly maintained self-hosted legacy deployment. It is not a ChemVault Lab SDK and does not translate API keys into Lab user sessions.
