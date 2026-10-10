/** Only allow same-site relative redirects, to avoid open redirects via `?next=`. */
export function safeNextPath(next: string | null | undefined, fallback = "/leads"): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) {
    return fallback;
  }
  return next;
}
