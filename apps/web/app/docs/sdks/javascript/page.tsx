import { DocsShell } from "../../docs-shell";
import { getDocsPage } from "../../docs-data";

export default function JavaScriptSdkDocsPage() {
  const page = getDocsPage("sdks/javascript");
  if (!page) return null;
  return <DocsShell page={page} />;
}
