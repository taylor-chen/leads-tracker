import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE, loginPath } from "@/lib/auth";

/**
 * Cheap gate for internal pages: no cookie → login. Token validity is still
 * enforced by the API on every request; pages redirect to login on a 401.
 */
export function middleware(request: NextRequest) {
  if (!request.cookies.get(SESSION_COOKIE)) {
    const next = request.nextUrl.pathname + request.nextUrl.search;
    return NextResponse.redirect(new URL(loginPath(next), request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/leads/:path*"],
};
