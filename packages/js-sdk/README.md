# ChemVault JavaScript SDK

TypeScript SDK for the ChemVault Extract developer API.

Package publishing is not enabled yet. Use local package installation during development:

```bash
npm install ./packages/js-sdk
```

```ts
import { ChemVault } from "@chemvault/sdk";

const client = new ChemVault({
  apiKey: "cv_live_xxx",
  baseUrl: "https://api.chemvault.science",
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

The SDK only calls the existing `/v1` API. It does not bypass plan limits, rate limits, API scopes, evidence validation, or review workflows.
