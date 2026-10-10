import "server-only";

import { cookies } from "next/headers";

export const SESSION_COOKIE = "leads_session";

export const sessionCookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  // Set COOKIE_SECURE=true when served over HTTPS (always, outside local dev).
  secure: process.env.COOKIE_SECURE === "true",
  path: "/",
};

export async function getSessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

/** Only allow same-site relative redirects, to avoid open redirects via `?next=`. */
export function safeNextPath(next: string | null | undefined, fallback = "/leads"): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) {
    return fallback;
  }
  return next;
}
