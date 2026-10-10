import { NextResponse } from "next/server";

import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";

export async function POST(request: Request) {
  // 303 so the browser follows the redirect with a GET after the form POST.
  const response = NextResponse.redirect(new URL("/login", request.url), 303);
  response.cookies.set(SESSION_COOKIE, "", { ...sessionCookieOptions, maxAge: 0 });
  return response;
}
