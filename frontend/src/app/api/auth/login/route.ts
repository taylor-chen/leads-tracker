import { NextResponse } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth";
import { backendFetch, errorMessage } from "@/lib/backend";
import { sessionCookieOptions } from "@/lib/session";

interface TokenResponse {
  access_token: string;
  expires_in: number;
}

/** Exchanges credentials for an API token and stores it in an httpOnly cookie. */
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body?.email || !body?.password) {
    return NextResponse.json(
      { error: { message: "Email and password are required" } },
      { status: 400 },
    );
  }

  const res = await backendFetch(
    "/api/v1/auth/login",
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: body.email, password: body.password }),
    },
    { auth: false },
  );
  if (!res.ok) {
    const message = res.status === 422 ? "Invalid email or password" : await errorMessage(res);
    return NextResponse.json({ error: { message } }, { status: res.status });
  }

  const token = (await res.json()) as TokenResponse;
  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE, token.access_token, {
    ...sessionCookieOptions,
    maxAge: token.expires_in,
  });
  return response;
}
