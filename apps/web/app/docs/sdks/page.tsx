import { DocsShell } from "../docs-shell";
import { getDocsPage } from "../docs-data";

export default function SdkDocsPage() {
  const page = getDocsPage("sdks");
  if (!page) return null;
  return <DocsShell page={page} />;
}
