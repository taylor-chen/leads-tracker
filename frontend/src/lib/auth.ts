// Auth helpers with no server-only dependencies, so client components and middleware can use them.

export const SESSION_COOKIE = "leads_session";

/** Only allow same-site relative redirects, to avoid open redirects via `?next=`. */
export function safeNextPath(next: string | null | undefined, fallback = "/leads"): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) {
    return fallback;
  }
  return next;
}

/** Login URL that returns to `next` after sign-in; `expired` shows the "session expired" notice. */
export function loginPath(next: string, { expired = false }: { expired?: boolean } = {}): string {
  const qs = new URLSearchParams();
  if (expired) qs.set("expired", "1");
  qs.set("next", next);
  return `/login?${qs}`;
}
