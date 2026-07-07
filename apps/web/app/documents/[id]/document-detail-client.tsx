"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type {
  AICostEstimate,
  AIExtractionJobResponse,
  Document,
  DocumentBlock,
  DocumentChunk,
  DocumentPage,
} from "@chemvault-extract/schemas";
import { Calculator, RefreshCw, Sparkles } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatDate, statusLabel } from "@/lib/format";

const visiblePipeline = ["queued", "parsing", "extracting", "validating", "normalizing", "review_ready"];

export function DocumentDetailClient({ initialDocument }: { initialDocument: Document }) {
  const [document, setDocument] = useState(initialDocument);
  const [pages, setPages] = useState<DocumentPage[]>([]);
  const [blocks, setBlocks] = useState<DocumentBlock[]>([]);
  const [tables, setTables] = useState<DocumentBlock[]>([]);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [startingExtraction, setStartingExtraction] = useState(false);
  const [normalizing, setNormalizing] = useState(false);
  const [estimatingCost, setEstimatingCost] = useState(false);
  const [costEstimate, setCostEstimate] = useState<AICostEstimate | null>(null);
  const latestJob = document.latestJob;
  const currentIndex = useMemo(
    () => visiblePipeline.findIndex((status) => status === latestJob?.status),
    [latestJob?.status],
  );
  const detectedSections = useMemo(() => getDetectedSections(blocks, chunks), [blocks, chunks]);

  const refresh = useCallback(async () => {
    try {
      const documentResponse = await fetch(`/api/documents/${document.id}`);
      const documentBody = await documentResponse.json();
      if (!documentResponse.ok) {
        throw new Error(documentBody.detail ?? "Unable to refresh document");
      }
      setDocument(documentBody as Document);

      const [pagesResponse, blocksResponse, tablesResponse, chunksResponse] = await Promise.all([
        fetch(`/api/documents/${document.id}/pages`),
        fetch(`/api/documents/${document.id}/blocks`),
        fetch(`/api/documents/${document.id}/tables`),
        fetch(`/api/documents/${document.id}/chunks`),
      ]);
      if (pagesResponse.ok) setPages((await pagesResponse.json()) as DocumentPage[]);
      if (blocksResponse.ok) setBlocks((await blocksResponse.json()) as DocumentBlock[]);
      if (tablesResponse.ok) setTables((await tablesResponse.json()) as DocumentBlock[]);
      if (chunksResponse.ok) setChunks((await chunksResponse.json()) as DocumentChunk[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to refresh document");
    }
  }, [document.id]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (latestJob?.status === "review_ready" || latestJob?.status === "failed") return;

    const interval = window.setInterval(() => {
      void refresh();
    }, 2000);

    return () => window.clearInterval(interval);
  }, [latestJob?.status, refresh]);

  const startAiExtraction = useCallback(async () => {
    const confirmed = window.confirm(
      "This will send selected document chunks to OpenAI for structured extraction and may incur API costs. Continue?",
    );
    if (!confirmed) return;
    setStartingExtraction(true);
    try {
      const response = await fetch(`/api/documents/${document.id}/extract-ai`, { method: "POST" });
      const body = (await response.json()) as unknown;
      if (!response.ok) {
        throw new Error(getErrorDetail(body, "Unable to start extraction"));
      }
      const extractionResponse = body as AIExtractionJobResponse;
      setDocument((current) => ({ ...current, latestJob: extractionResponse.job }));
      setCostEstimate(extractionResponse.estimatedCost);
      setError(null);
      void refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start extraction");
    } finally {
      setStartingExtraction(false);
    }
  }, [document.id, refresh]);

  const startNormalization = useCallback(async () => {
    setNormalizing(true);
    try {
      const response = await fetch(`/api/documents/${document.id}/normalize`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({}),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "Unable to run normalization");
      }
      void refresh();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run normalization");
    } finally {
      setNormalizing(false);
    }
  }, [document.id, refresh]);

  const estimateCost = useCallback(async () => {
    setEstimatingCost(true);
    try {
      const response = await fetch(`/api/documents/${document.id}/estimate-ai-cost`, { method: "POST" });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "Unable to estimate cost");
      }
      setCostEstimate(body as AICostEstimate);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to estimate cost");
    } finally {
      setEstimatingCost(false);
    }
  }, [document.id]);

  return (
    <div className="flex flex-col gap-4">
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Refresh failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Tabs defaultValue="overview" className="flex flex-col gap-4">
        <TabsList className="w-full justify-start overflow-x-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="pages">Pages</TabsTrigger>
          <TabsTrigger value="blocks">Blocks</TabsTrigger>
          <TabsTrigger value="chunks">Chunks</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-0">
          <div className="grid gap-6">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
              <DocumentMetadataCard
                document={document}
                pageCount={pages.length}
                blockCount={blocks.length}
                tableCount={tables.length}
                chunkCount={chunks.length}
                sections={detectedSections}
              />
              <JobStatusCard
                latestJob={latestJob}
                currentIndex={currentIndex}
                onRefresh={refresh}
                onStartAiExtraction={startAiExtraction}
                onEstimateCost={estimateCost}
                onNormalize={startNormalization}
                startingExtraction={startingExtraction}
                normalizing={normalizing}
                estimatingCost={estimatingCost}
                costEstimate={costEstimate}
              />
            </div>
            <DocumentTimeline document={document} pageCount={pages.length} chunkCount={chunks.length} />
          </div>
        </TabsContent>

        <TabsContent value="preview" className="mt-0">
          <ParsedPreviewPanel pages={pages} blocks={blocks} />
        </TabsContent>

        <TabsContent value="pages" className="mt-0">
          <PagesPanel pages={pages} />
        </TabsContent>

        <TabsContent value="blocks" className="mt-0">
          <BlocksPanel blocks={blocks} />
        </TabsContent>

        <TabsContent value="chunks" className="mt-0">
          <ChunksPanel chunks={chunks} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function DocumentTimeline({
  document,
  pageCount,
  chunkCount,
}: {
  document: Document;
  pageCount: number;
  chunkCount: number;
}) {
  const latestStatus = document.latestJob?.status;
  const steps = [
    { label: "Uploaded", complete: true, detail: formatDate(document.createdAt) },
    { label: "Parsed", complete: pageCount > 0 || document.status === "parsed" || document.status === "review_ready", detail: `${pageCount} pages` },
    { label: "AI extracted", complete: ["validating", "normalizing", "review_ready"].includes(latestStatus ?? ""), detail: latestStatus ?? "not started" },
    { label: "Normalized", complete: ["normalizing", "review_ready"].includes(latestStatus ?? ""), detail: `${chunkCount} chunks` },
    { label: "Reviewed", complete: document.status === "review_ready", detail: document.status },
    { label: "Exported", complete: false, detail: "pending export job" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Document timeline</CardTitle>
        <CardDescription>High-level workflow from upload to export.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-6">
        {steps.map((step) => (
          <div key={step.label} className="rounded-md border bg-white p-3">
            <div className="mb-3 flex items-center gap-2">
              <div className={step.complete ? "size-2.5 rounded-full bg-primary" : "size-2.5 rounded-full border bg-background"} />
              <span className="text-sm font-medium">{step.label}</span>
            </div>
            <p className="text-xs text-muted-foreground">{step.detail}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function DocumentMetadataCard({
  document,
  pageCount,
  blockCount,
  tableCount,
  chunkCount,
  sections,
}: {
  document: Document;
  pageCount: number;
  blockCount: number;
  tableCount: number;
  chunkCount: number;
  sections: string[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{document.originalFilename}</CardTitle>
        <CardDescription>Document ID: {document.id}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2">
        <DetailItem label="Stored filename" value={document.filename} />
        <DetailItem label="File type" value={document.fileType.toUpperCase()} />
        <DetailItem label="MIME type" value={document.mimeType} />
        <DetailItem label="Uploaded" value={formatDate(document.createdAt)} />
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-muted-foreground">Document status</span>
          <StatusBadge status={document.status} />
        </div>
        <DetailItem label="Storage key" value={document.storageKey} mono />
        <DetailItem label="Parsed pages" value={String(pageCount)} />
        <DetailItem label="Parsed blocks" value={String(blockCount)} />
        <DetailItem label="Parsed tables" value={String(tableCount)} />
        <DetailItem label="Chunks" value={String(chunkCount)} />
        <div className="flex min-w-0 flex-col gap-2 sm:col-span-2">
          <span className="text-xs font-medium text-muted-foreground">Detected sections</span>
          {sections.length === 0 ? (
            <span className="text-sm text-muted-foreground">No sections detected yet.</span>
          ) : (
            <div className="flex flex-wrap gap-2">
              {sections.map((section) => (
                <Badge key={section} variant="secondary">
                  {section}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function JobStatusCard({
  latestJob,
  currentIndex,
  onRefresh,
  onStartAiExtraction,
  onNormalize,
  onEstimateCost,
  startingExtraction,
  normalizing,
  estimatingCost,
  costEstimate,
}: {
  latestJob: Document["latestJob"];
  currentIndex: number;
  onRefresh: () => void;
  onStartAiExtraction: () => void;
  onNormalize: () => void;
  onEstimateCost: () => void;
  startingExtraction: boolean;
  normalizing: boolean;
  estimatingCost: boolean;
  costEstimate: AICostEstimate | null;
}) {
  const activeJob = latestJob && !["review_ready", "failed"].includes(latestJob.status);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between gap-3 text-base">
          Extraction job
          <StatusBadge status={latestJob?.status} />
        </CardTitle>
        <CardDescription>{latestJob ? `Job ID: ${latestJob.id}` : "No extraction job"}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Alert>
          <AlertTitle>AI extraction may process submitted content through third-party AI services.</AlertTitle>
          <AlertDescription>
            Do not submit sensitive personal information, confidential data, or content you do not have permission to process. AI
            outputs may be inaccurate and should be reviewed before use. Only selected chunks are sent, with references excluded
            and long chunks truncated. See the{" "}
            <Link className="underline" href="https://chemvault.science/privacy">
              Privacy Policy
            </Link>
            .
          </AlertDescription>
        </Alert>
        {latestJob ? (
          <>
            <div className="flex flex-col gap-3">
              {visiblePipeline.map((status, index) => {
                const complete = latestJob.status === "review_ready" || index <= currentIndex;
                return (
                  <div key={status} className="flex items-center gap-3">
                    <div
                      className={
                        complete
                          ? "size-2.5 rounded-full bg-primary"
                          : "size-2.5 rounded-full border border-border bg-background"
                      }
                    />
                    <span className={complete ? "text-sm" : "text-sm text-muted-foreground"}>{statusLabel(status)}</span>
                  </div>
                );
              })}
            </div>
            {latestJob.error ? (
              <Alert variant="destructive">
                <AlertTitle>Job failed</AlertTitle>
                <AlertDescription>{latestJob.error}</AlertDescription>
              </Alert>
            ) : null}
          </>
        ) : (
          <p className="text-sm text-muted-foreground">No job has been created for this document.</p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={onEstimateCost} disabled={estimatingCost}>
            <Calculator data-icon="inline-start" />
            Estimate AI Cost
          </Button>
          <Button variant="default" size="sm" onClick={onStartAiExtraction} disabled={Boolean(activeJob) || startingExtraction}>
            <Sparkles data-icon="inline-start" />
            Run AI Extraction
          </Button>
          <Button variant="outline" size="sm" onClick={onNormalize} disabled={normalizing}>
            Run Normalization
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link href="/documents">Documents</Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link href={latestJob ? `/documents/${latestJob.documentId}/review` : "/documents"}>Review</Link>
          </Button>
          <Button variant="outline" size="sm" onClick={onRefresh}>
            <RefreshCw data-icon="inline-start" />
            Refresh
          </Button>
        </div>
        {costEstimate ? (
          <div className="grid gap-3 rounded-md border p-3 text-sm sm:grid-cols-2 xl:grid-cols-5">
            <DetailItem label="Estimated cost" value={`$${costEstimate.estimatedCostUsd.toFixed(4)}`} />
            <DetailItem label="Selected chunks" value={String(costEstimate.selectedChunks)} />
            <DetailItem label="Input tokens" value={String(costEstimate.estimatedInputTokens)} />
            <DetailItem label="Output tokens" value={String(costEstimate.estimatedOutputTokens)} />
            <DetailItem label="Model" value={costEstimate.model} />
            <p className="text-xs text-muted-foreground sm:col-span-2 xl:col-span-5">{costEstimate.warning}</p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function ParsedPreviewPanel({ pages, blocks }: { pages: DocumentPage[]; blocks: DocumentBlock[] }) {
  const previews = useMemo(() => buildParsedPreview(pages, blocks), [pages, blocks]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Parsed preview</CardTitle>
        <CardDescription>Text grouped by page and detected scientific section</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {previews.length === 0 ? (
          <EmptyMessage message="No parsed text preview yet." />
        ) : (
          previews.map((page) => (
            <div key={page.pageNumber} className="flex flex-col gap-4 rounded-md border p-4">
              <h3 className="text-sm font-medium">Page {page.pageNumber}</h3>
              {page.sections.map((section) => (
                <section key={`${page.pageNumber}-${section.section}`} className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">Section: {section.section}</Badge>
                  </div>
                  <p className="max-h-80 overflow-auto whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                    {section.text}
                  </p>
                </section>
              ))}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function PagesPanel({ pages }: { pages: DocumentPage[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Parsed pages</CardTitle>
        <CardDescription>{pages.length} page records saved for this document</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {pages.length === 0 ? (
          <EmptyMessage message="No parsed pages yet." />
        ) : (
          pages.map((page) => (
            <div key={page.id} className="flex flex-col gap-2 rounded-md border p-4">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-medium">Page {page.pageNumber}</h3>
                <span className="text-xs text-muted-foreground">
                  {page.width && page.height ? `${Math.round(page.width)} x ${Math.round(page.height)}` : "text only"}
                </span>
              </div>
              <p className="max-h-64 overflow-auto whitespace-pre-wrap text-sm text-muted-foreground">
                {page.text || "No text extracted for this page."}
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function BlocksPanel({ blocks }: { blocks: DocumentBlock[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Parsed blocks</CardTitle>
        <CardDescription>{blocks.length} headings, paragraphs, and tables saved from the parser</CardDescription>
      </CardHeader>
      <CardContent>
        {blocks.length === 0 ? (
          <EmptyMessage message="No parsed blocks yet." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Section</TableHead>
                <TableHead>Page</TableHead>
                <TableHead>Text</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {blocks.map((block) => (
                <TableRow key={block.id}>
                  <TableCell>
                    <Badge variant={block.blockType === "table" ? "default" : "secondary"}>{block.blockType}</Badge>
                  </TableCell>
                  <TableCell>{block.section || "Unsectioned"}</TableCell>
                  <TableCell>{block.pageNumber ?? "-"}</TableCell>
                  <TableCell className="max-w-[560px]">
                    <span className="line-clamp-3 text-sm text-muted-foreground">{block.text || block.html || "-"}</span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function ChunksPanel({ chunks }: { chunks: DocumentChunk[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Chunks</CardTitle>
        <CardDescription>{chunks.length} section-based chunks prepared for future AI extraction</CardDescription>
      </CardHeader>
      <CardContent>
        {chunks.length === 0 ? (
          <EmptyMessage message="No chunks yet." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Index</TableHead>
                <TableHead>Section</TableHead>
                <TableHead>Pages</TableHead>
                <TableHead>Tokens</TableHead>
                <TableHead>Preview</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {chunks.map((chunk) => (
                <TableRow key={chunk.id}>
                  <TableCell>{chunk.chunkIndex}</TableCell>
                  <TableCell>{chunk.section || "Unsectioned"}</TableCell>
                  <TableCell>{formatPageRange(chunk)}</TableCell>
                  <TableCell>{chunk.tokenCount ?? "-"}</TableCell>
                  <TableCell className="max-w-[620px]">
                    <span className="line-clamp-3 text-sm text-muted-foreground">{chunk.text}</span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

type ParsedPreviewPage = {
  pageNumber: number;
  sections: Array<{
    section: string;
    text: string;
  }>;
};

function getDetectedSections(blocks: DocumentBlock[], chunks: DocumentChunk[]): string[] {
  const sections: string[] = [];
  const seen = new Set<string>();
  for (const section of [...blocks.map((block) => block.section), ...chunks.map((chunk) => chunk.section)]) {
    if (!section || section === "Unsectioned" || seen.has(section)) continue;
    seen.add(section);
    sections.push(section);
  }
  return sections;
}

function buildParsedPreview(pages: DocumentPage[], blocks: DocumentBlock[]): ParsedPreviewPage[] {
  const grouped = new Map<number, Map<string, string[]>>();
  for (const block of blocks) {
    if (!block.text || block.blockType === "table" || block.blockType === "heading") continue;
    const pageNumber = block.pageNumber ?? 1;
    const section = block.section ?? "Unsectioned";
    const bySection = grouped.get(pageNumber) ?? new Map<string, string[]>();
    const texts = bySection.get(section) ?? [];
    texts.push(block.text);
    bySection.set(section, texts);
    grouped.set(pageNumber, bySection);
  }

  if (grouped.size === 0) {
    return pages
      .filter((page) => Boolean(page.text?.trim()))
      .map((page) => ({
        pageNumber: page.pageNumber,
        sections: [{ section: "Unsectioned", text: page.text?.trim() ?? "" }],
      }));
  }

  return Array.from(grouped.entries())
    .sort(([left], [right]) => left - right)
    .map(([pageNumber, bySection]) => ({
      pageNumber,
      sections: Array.from(bySection.entries()).map(([section, texts]) => ({
        section,
        text: texts.join("\n\n"),
      })),
    }));
}

function formatPageRange(chunk: DocumentChunk): string {
  if (!chunk.pageStart && !chunk.pageEnd) return "-";
  if (chunk.pageStart === chunk.pageEnd) return String(chunk.pageStart);
  return `${chunk.pageStart ?? "?"}-${chunk.pageEnd ?? "?"}`;
}

function getErrorDetail(value: unknown, fallback: string): string {
  if (
    value &&
    typeof value === "object" &&
    "detail" in value &&
    typeof (value as { detail?: unknown }).detail === "string"
  ) {
    return (value as { detail: string }).detail;
  }
  return fallback;
}

function EmptyMessage({ message }: { message: string }) {
  return (
    <div className="flex min-h-36 items-center justify-center rounded-md border border-dashed">
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

function DetailItem({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className={mono ? "break-all font-mono text-xs" : "break-words text-sm"}>{value}</span>
    </div>
  );
}
