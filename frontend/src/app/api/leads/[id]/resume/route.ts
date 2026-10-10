import { NextResponse } from "next/server";

import { loginPath } from "@/lib/auth";
import { backendFetch, errorMessage } from "@/lib/backend";

/** Authenticated: streams a lead's resume from the API using the session token. */
export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const res = await backendFetch(`/api/v1/leads/${encodeURIComponent(id)}/resume`);

  if (res.status === 401) {
    const login = loginPath(`/leads/${id}`, { expired: true });
    return NextResponse.redirect(new URL(login, request.url));
  }
  if (!res.ok || !res.body) {
    return NextResponse.json(
      { error: { message: await errorMessage(res) } },
      { status: res.status || 502 },
    );
  }

  const headers = new Headers();
  for (const name of ["content-type", "content-length", "content-disposition"]) {
    const value = res.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set("cache-control", "private, no-store");
  return new NextResponse(res.body, { status: 200, headers });
}
