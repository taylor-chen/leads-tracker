import "server-only";

import { redirect } from "next/navigation";

import { getSessionToken } from "@/lib/session";

/** Base URL of the FastAPI service, reachable from the Next.js server only. */
const API_URL = process.env.API_URL ?? "http://localhost:8000";

/** A non-2xx response from the API, other than a 401 (which redirects to login). */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

/** Best-effort human-readable message from an API error response. */
export async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body?.error?.message ?? body?.detail ?? res.statusText;
  } catch {
    return res.statusText || "Request failed";
  }
}

/**
 * Call the backend from the server. Attaches the session's bearer token unless
 * `auth: false`. Returns the raw Response so callers can stream or inspect it.
 */
export async function backendFetch(
  path: string,
  init: RequestInit = {},
  { auth = true }: { auth?: boolean } = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (auth) {
    const token = await getSessionToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });
}

/**
 * Fetch JSON for an authenticated page. Redirects to the login page when the
 * session is missing or expired; throws ApiError for other failures.
 */
export async function backendJsonOrLogin<T>(path: string, returnTo: string): Promise<T> {
  const res = await backendFetch(path);
  if (res.status === 401) {
    redirect(`/login?expired=1&next=${encodeURIComponent(returnTo)}`);
  }
  if (!res.ok) {
    throw new ApiError(res.status, await errorMessage(res));
  }
  return (await res.json()) as T;
}
