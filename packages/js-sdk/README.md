# ChemVault Extract JavaScript SDK (retired)

The hosted ChemVault Extract API has been retired. Current upload, analysis, review, search, and export workflows live in [ChemVault Lab](https://lab.chemvault.science).

Package publishing is not enabled yet. Use local package installation during development:

```bash
npm install ./packages/js-sdk
```

```ts
import { ChemVault } from "@chemvault/sdk";

const client = new ChemVault({
  apiKey: "legacy-self-hosted-key",
  baseUrl: "http://localhost:8000",
});

const project = await client.projects.create({ name: "Organic synthesis" });
const document = await client.documents.upload({
  projectId: project.id,
  file,
  filename: "paper.pdf",
});
const estimate = await client.documents.estimate(document.document_id);
const job = await client.documents.extract(document.document_id);
const records = await client.documents.records(document.document_id);
```

There is intentionally no hosted default base URL. Use this package only for an explicitly maintained self-hosted legacy deployment. It is not a ChemVault Lab SDK and does not translate the retired API-key contract into a Lab user session.
