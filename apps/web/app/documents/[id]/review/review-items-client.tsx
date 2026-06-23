"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReviewItem } from "@chemvault-extract/schemas";
import { Check, Pencil, RefreshCw, X } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface ExtractedPayload {
  recordType?: string;
  raw?: Record<string, unknown>;
  normalized?: Record<string, unknown>;
  validationStatus?: string | null;
  validationWarnings?: unknown;
}

const EMPTY_RECORD: ExtractedPayload = {
  raw: {},
  normalized: {},
};

export function ReviewItemsClient({ documentId }: { documentId: string }) {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const counts = useMemo(
    () => ({
      pending: items.filter((item) => item.status === "pending").length,
      needsReview: items.filter((item) => item.status === "needs_review").length,
      approved: items.filter((item) => item.status === "approved").length,
      rejected: items.filter((item) => item.status === "rejected").length,
    }),
    [items],
  );

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(`/api/documents/${documentId}/review-items`, { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "Unable to load review items");
      }
      setItems(body as ReviewItem[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load review items");
    }
  }, [documentId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function patchItem(id: string, payload: { status?: string; extractedData?: Record<string, unknown> }) {
    const response = await fetch(`/api/review-items/${id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail ?? "Unable to update review item");
    }
    setItems((current) => current.map((item) => (item.id === id ? (body as ReviewItem) : item)));
  }

  async function approve(id: string) {
    try {
      await patchItem(id, { status: "approved" });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to approve item");
    }
  }

  async function reject(id: string) {
    try {
      await patchItem(id, { status: "rejected" });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reject item");
    }
  }

  async function saveEdit(item: ReviewItem) {
    try {
      const extractedData = JSON.parse(draft) as Record<string, unknown>;
      await patchItem(item.id, { extractedData });
      setEditingId(null);
      setDraft("");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid JSON edit");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Review update failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div className="flex flex-col gap-1.5">
            <CardTitle>Review queue</CardTitle>
            <CardDescription>
              {items.length} structured extraction items. Offline mode produces no items until an AI provider is connected.
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={refresh}>
            <RefreshCw data-icon="inline-start" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Pending {counts.pending}</Badge>
            <Badge variant="outline">Needs review {counts.needsReview}</Badge>
            <Badge>Approved {counts.approved}</Badge>
            <Badge variant="destructive">Rejected {counts.rejected}</Badge>
          </div>

          {items.length === 0 ? (
            <div className="flex min-h-40 items-center justify-center rounded-md border border-dashed">
              <p className="text-sm text-muted-foreground">No review items yet.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {items.map((item) => {
                const payload = extractPayload(item);
                return (
                  <div key={item.id} className="flex flex-col gap-4 rounded-md border p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="flex flex-col gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="outline">{item.recordType}</Badge>
                          <StatusBadge status={item.status} />
                          <ValidationBadge status={
                            payload.validationStatus && payload.validationStatus !== item.status
                              ? payload.validationStatus
                              : item.status
                          } />
                          {item.confidence !== null ? (
                            <Badge variant="secondary">Confidence {item.confidence.toFixed(2)}</Badge>
                          ) : null}
                        </div>
                        <p className="text-xs text-muted-foreground">Review item ID: {item.id}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" onClick={() => approve(item.id)}>
                          <Check data-icon="inline-start" />
                          Approve
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => reject(item.id)}>
                          <X data-icon="inline-start" />
                          Reject
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingId(item.id);
                            setDraft(JSON.stringify(item.extractedData ?? {}, null, 2));
                          }}
                        >
                          <Pencil data-icon="inline-start" />
                          Edit
                        </Button>
                      </div>
                    </div>

                    {editingId === item.id ? (
                      <div className="flex flex-col gap-2">
                        <span className="text-xs font-medium text-muted-foreground">Edit extracted data JSON</span>
                        <textarea
                          className="min-h-52 rounded-md border bg-background p-3 font-mono text-xs"
                          value={draft}
                          onChange={(event) => setDraft(event.target.value)}
                        />
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => saveEdit(item)}>
                            Save edit
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => setEditingId(null)}>
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : null}

                    <div className="grid gap-4 lg:grid-cols-2">
                      <section className="flex flex-col gap-2">
                        <span className="text-xs font-medium text-muted-foreground">Raw values</span>
                        <JsonBlock value={payload.raw} />
                      </section>

                      <section className="flex flex-col gap-2">
                        <span className="text-xs font-medium text-muted-foreground">Normalized values</span>
                        <JsonBlock value={payload.normalized} />
                        <ValidationPanel
                          status={payload.validationStatus ?? "needs_review"}
                          warnings={payload.validationWarnings}
                        />
                      </section>

                      <section className="lg:col-span-2">
                        <span className="text-xs font-medium text-muted-foreground">Evidence</span>
                        <EvidencePanel evidence={item.evidence} />
                      </section>

                      {item.recordType === "chemical_entity" ? (
                        <section className="lg:col-span-2">
                          <span className="text-xs font-medium text-muted-foreground">PubChem / RDKit enrichment</span>
                          <EnrichmentPanel normalized={payload.normalized} />
                        </section>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function extractPayload(item: ReviewItem): ExtractedPayload {
  const payload = item.extractedData;
  if (!payload || typeof payload !== "object") {
    return EMPTY_RECORD;
  }
  const raw = payload.raw;
  const normalized = payload.normalized;
  return {
    recordType: (item.recordType as string | undefined) ?? "",
    raw: isRecord(raw) ? raw : {},
    normalized: isRecord(normalized) ? normalized : {},
    validationStatus:
      typeof payload.validationStatus === "string"
        ? payload.validationStatus
        : (typeof payload.validationStatus === "object" || payload.validationStatus == null
            ? null
            : String(payload.validationStatus)),
    validationWarnings: payload.validationWarnings,
  };
}

function ValidationBadge({ status }: { status: string }) {
  const normalized = status === "valid" ? "valid" : status;
  return <Badge variant={normalized === "valid" ? "default" : "secondary"}>{normalized}</Badge>;
}

function ValidationPanel({ status, warnings }: { status: string; warnings: unknown }) {
  const warningList: string[] = toStringArray(warnings);
  return (
    <div className="rounded-md bg-muted p-3 text-xs">
      <p className="font-medium">Validation status: {status}</p>
      {warningList.length > 0 ? (
        <div className="mt-2">
          <p className="font-medium">Warnings:</p>
          <ul className="list-disc space-y-1 pl-4 text-muted-foreground">
            {warningList.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function EvidencePanel({ evidence }: { evidence: Record<string, unknown> | null | undefined }) {
  const quote = (evidence?.quote as string | undefined) ?? "No evidence quote.";
  const page = evidence?.page;
  const section = evidence?.section;
  const chunkId = evidence?.chunkId ?? evidence?.chunk_id;
  return (
    <div className="rounded-md bg-muted p-3 text-sm">
      <p className="mb-3 whitespace-pre-wrap text-muted-foreground">{quote}</p>
      <div className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
        <span>Page: {page != null ? String(page) : "-"}</span>
        <span>Section: {typeof section === "string" && section.length > 0 ? section : "-"}</span>
        <span className="break-all sm:col-span-2">Chunk: {String(chunkId ?? "-")}</span>
      </div>
    </div>
  );
}

function EnrichmentPanel({ normalized }: { normalized: Record<string, unknown> | undefined }) {
  const pubchemCid = normalized?.pubchemCid ?? "-";
  const molecularWeight = normalized?.molecularWeight ?? "-";
  const molecularFormula = normalized?.molecularFormula ?? normalized?.normalizedFormula ?? "-";
  const canonicalSmiles = normalized?.canonicalSmiles ?? "-";
  const inchiKey = normalized?.inchiKey ?? "-";
  const enrichmentStatus = normalized?.enrichmentStatus ?? "-";
  const enrichmentSource = normalized?.enrichmentSource ?? "-";
  const normalizedAmount = normalized?.normalizedAmount ?? "-";

  return (
    <div className="grid gap-2 rounded-md bg-muted p-3 text-xs sm:grid-cols-2">
      <div>PubChem CID: {String(pubchemCid)}</div>
      <div>Canonical SMILES: {String(canonicalSmiles)}</div>
      <div>InChI Key: {String(inchiKey)}</div>
      <div>Molecular formula: {String(molecularFormula)}</div>
      <div>Molecular weight: {String(molecularWeight)}</div>
      <div>Enrichment status: {String(enrichmentStatus)}</div>
      <div>Enrichment source: {String(enrichmentSource)}</div>
      <div>Normalized amount: {String(normalizedAmount)}</div>
    </div>
  );
}

function JsonBlock({ value }: { value: Record<string, unknown> | undefined }) {
  return <pre className="max-h-72 overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(value ?? {}, null, 2)}</pre>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (typeof item === "string") return item;
      if (item == null) return null;
      return JSON.stringify(item);
    })
    .filter((item): item is string => item !== null && item.length > 0);
}
