export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function statusLabel(value: string | null | undefined): string {
  if (!value) return "not started";
  return value.replaceAll("_", " ");
}
