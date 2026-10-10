import { NextResponse } from "next/server";

/**
 * Redirect to a same-origin path with a relative `Location` header.
 *
 * Don't build redirect targets from `request.url`: the standalone server fills it in from its own
 * bind address (`HOSTNAME`/`PORT`, e.g. `0.0.0.0:10000`), not the public host behind the proxy.
 * The browser resolves a relative `Location` against the URL it actually requested.
 * Route handlers only: middleware rejects a relative `Location`, and already relativizes
 * same-origin redirects itself.
 */
export function redirectToPath(
  path: string,
  params: Record<string, string> = {},
  status: 303 | 307 = 307,
): NextResponse {
  const query = new URLSearchParams(params).toString();
  return new NextResponse(null, {
    status,
    headers: { Location: query ? `${path}?${query}` : path },
  });
}
