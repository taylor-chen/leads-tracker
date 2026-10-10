import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

/** Public: forwards the lead form (multipart, incl. resume) to the API. */
export async function POST(request: Request) {
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return NextResponse.json(
      { error: { code: "bad_request", message: "Expected multipart form data" } },
      { status: 400 },
    );
  }

  const res = await backendFetch("/api/v1/leads", { method: "POST", body: form }, { auth: false });
  return new NextResponse(await res.text(), {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") ?? "application/json" },
  });
}
