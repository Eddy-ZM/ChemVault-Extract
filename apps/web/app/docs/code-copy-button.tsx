"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";

export function CodeCopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <Button variant="outline" size="sm" onClick={copy}>
      {copied ? <Check data-icon="inline-start" /> : <Copy data-icon="inline-start" />}
      {copied ? "Copied" : "Copy"}
    </Button>
  );
}
