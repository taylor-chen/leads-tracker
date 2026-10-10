import { NextResponse } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth";
import { backendFetch } from "@/lib/backend";
import { getSessionToken, sessionCookieOptions } from "@/lib/session";

/** Signs out: revokes the API token, clears the cookie and redirects to /login. */
export async function POST(request: Request) {
  // Revoke the token server-side so a copied token stops working too. The cookie is cleared
  // regardless, so a failed or unreachable API never leaves the user stuck signed in.
  if (await getSessionToken()) {
    try {
      const res = await backendFetch("/api/v1/auth/logout", { method: "POST" });
      if (!res.ok && res.status !== 401) {
        console.error(`Token revocation failed with status ${res.status}`);
      }
    } catch (err) {
      console.error("Token revocation failed", err);
    }
  }

  // 303 so the browser follows the redirect with a GET after the form POST.
  const response = NextResponse.redirect(new URL("/login", request.url), 303);
  response.cookies.set(SESSION_COOKIE, "", { ...sessionCookieOptions, maxAge: 0 });
  return response;
}
