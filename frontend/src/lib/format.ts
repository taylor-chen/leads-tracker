const dateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

/** Format an ISO timestamp for display, or "—" when there isn't one. */
export function formatDateTime(iso: string | null): string {
  return iso ? dateFormatter.format(new Date(iso)) : "—";
}

/** Format a file size, e.g. "512 B", "34 KB", "1.2 MB". */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
