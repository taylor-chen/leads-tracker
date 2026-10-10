import { NextResponse, type NextRequest } from "next/server";

// Kept in sync with SESSION_COOKIE in lib/session.ts (middleware can't import server-only modules).
const SESSION_COOKIE = "leads_session";

/**
 * Cheap gate for internal pages: no cookie → login. Token validity is still
 * enforced by the API on every request; pages redirect to login on a 401.
 */
export function middleware(request: NextRequest) {
  if (!request.cookies.get(SESSION_COOKIE)) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname + request.nextUrl.search);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/leads/:path*"],
};
