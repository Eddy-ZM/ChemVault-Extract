# ChemVault Extract

ChemVault Extract is a ChemVault product for turning chemistry papers, lab reports, instrument exports, and research spreadsheets into structured, searchable, reviewable research data.

This repository currently provides the public website and the authenticated web application. It does not include a separate native mobile or desktop app.

## Product Scope

ChemVault Extract is designed for researchers, students, lab teams, and technical teams that need to organize chemistry documents and extracted scientific records in one workspace.

The product supports:

- Public product website for discovery, pricing, documentation, security information, and contact.
- Authenticated web application for document upload, extraction, review, search, exports, usage, billing, teams, and settings.
- Developer-facing account areas for API keys, usage visibility, request logs, webhook settings, and SDK documentation.

## Public Website

The public website introduces the ChemVault Extract product and helps visitors understand whether it fits their research workflow.

Main public areas:

- Home page with product positioning and primary calls to action.
- Features page describing document ingestion, structured extraction, evidence review, search, export, and team collaboration.
- Pricing page with plan options and subscription actions.
- Demo page with a guided sample workflow.
- Use cases page for individual researchers, student projects, labs, and data teams.
- Security page covering account access, data handling, user-controlled keys, and operational safeguards.
- Documentation pages for product usage, developer access, SDKs, and integration guidance.
- Contact page for product or support inquiries.
- Login and registration entry points connected to ChemVault account access.

## Web App

The authenticated Web App is the main working environment for ChemVault Extract users.

### Dashboard

The dashboard gives users a quick view of recent activity and common actions:

- Upload documents.
- Start batch workflows.
- Continue review work.
- Search extracted records.
- Create exports.
- View recent document and job status.

### Documents

The document workspace lets users manage source files and track their processing state.

Supported user workflows include:

- Upload a single document.
- Upload multiple documents in a batch.
- View document metadata and processing status.
- Inspect parsed pages, blocks, tables, and chunks where available.
- Estimate extraction cost before running AI extraction.
- Start AI extraction for eligible documents.
- Follow document progress from upload through review and export.

Supported document types include:

- PDF
- DOCX
- CSV
- XLSX
- TXT
- MD

### Extraction And Review

ChemVault Extract helps users convert research documents into structured chemistry records while keeping review in the workflow.

User-facing extraction and review features include:

- Structured extraction for document metadata, chemical entities, reactions, and measurements.
- Evidence-backed review items linked to the source document context.
- Review queues for pending items.
- Item-level approve, reject, and edit actions.
- Normalized record views after extraction.
- Re-review and renormalization actions for selected records.

### Search And Database

The app includes a research database view and search experience for extracted records.

Users can:

- Browse extracted chemistry records.
- Search across available projects and documents.
- Filter results by record type and context.
- Review evidence previews from source documents.
- Move from search results into review or export workflows.

### Exports

The export area helps users package reviewed research data for downstream use.

Export features include:

- Create exports from available records.
- Choose common data formats such as CSV, JSON, and XLSX.
- View export history and export status.
- Download completed export files.
- See review warnings before exporting data that may still need human validation.

### Projects And Workspaces

ChemVault Extract supports both personal and team-oriented organization.

Users can:

- Create projects for separate research efforts.
- Manage team workspaces.
- Invite workspace members.
- Assign workspace roles.
- Use shared project access for lab or team workflows.
- Keep personal and team projects separated.

Workspace roles support owner, admin, member, and viewer use cases.

### Batch Workflows

Batch workflows help users process larger document sets.

Available batch features include:

- Multi-file upload.
- Batch status tracking.
- Batch AI extraction for eligible plans.
- Progress views for each batch.
- Cancel queued work where supported.
- Retry failed batch items.

### Account, Usage, And Billing

The account area gives users visibility and control over subscription and usage settings.

Users can:

- View account details.
- Review current-month usage.
- Manage billing through the billing area.
- Start paid plan checkout where available.
- Open the billing portal for subscription management.
- See plan-related limits for documents, projects, storage, AI extraction, batch workflows, and exports.

### AI Settings

ChemVault Extract supports user-facing AI settings for extraction workflows.

Users can:

- Use platform-managed extraction access when available.
- Add a supported user-provided AI provider key when enabled.
- Test a saved key.
- Remove a saved key.
- See masked key status without exposing the full key after saving.

### Developer Settings

Developer-facing features are available for users who want to connect ChemVault Extract with external systems.

Users can:

- Create and revoke API keys.
- View developer usage.
- View request logs.
- Configure webhook endpoints.
- Rotate webhook secrets.
- Send test webhooks.
- Inspect webhook delivery history and delivery detail.
- Read JavaScript and Python SDK documentation.

### Security And Access

The app includes user-facing access and safety controls designed for research data workflows.

Key user-visible safeguards include:

- Login-protected application pages.
- Project and workspace access boundaries.
- Role-based workspace permissions.
- Masked API key displays.
- Encrypted storage flow for user-provided AI keys.
- Billing-gated and plan-gated capabilities.
- Usage limits for AI extraction, documents, projects, storage, exports, and batch workflows.
- Human review before relying on extracted records.

## Product Pages

Public pages:

- `/`
- `/features`
- `/pricing`
- `/demo`
- `/use-cases`
- `/security`
- `/docs`
- `/contact`
- `/login`
- `/register`

Authenticated app pages:

- `/dashboard`
- `/documents`
- `/documents/upload`
- `/documents/batch-upload`
- `/documents/{document_id}`
- `/documents/{document_id}/review`
- `/review`
- `/database`
- `/search`
- `/exports`
- `/workspaces`
- `/workspaces/new`
- `/workspaces/{workspace_id}`
- `/workspaces/{workspace_id}/members`
- `/projects/new`
- `/batch`
- `/batch/{batch_job_id}`
- `/usage`
- `/settings`
- `/settings/ai`
- `/settings/api-keys`
- `/settings/webhooks`
- `/developers`
- `/developers/logs`
- `/developers/usage`
- `/account`
- `/account/billing`

## License

This repository is source-available but not open source. Public visibility is for review and reference only; no rights are granted to use, copy, modify, distribute, host, deploy, or create derivative works without prior written permission from Ziwen Mu or the repository owner.

See [LICENSE](./LICENSE). All rights reserved.
