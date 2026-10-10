import "server-only";

import { cookies } from "next/headers";

export const SESSION_COOKIE = "leads_session";

/** Options for setting (or, with `maxAge: 0`, clearing) the session cookie. */
export const sessionCookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  // Set COOKIE_SECURE=true when served over HTTPS (always, outside local dev).
  secure: process.env.COOKIE_SECURE === "true",
  path: "/",
};

/** The API bearer token stored in the session cookie, if any. */
export async function getSessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}
