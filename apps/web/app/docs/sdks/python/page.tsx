import { DocsShell } from "../../docs-shell";
import { getDocsPage } from "../../docs-data";

export default function PythonSdkDocsPage() {
  const page = getDocsPage("sdks/python");
  if (!page) return null;
  return <DocsShell page={page} />;
}
