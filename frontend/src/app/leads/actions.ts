"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { backendFetch, errorMessage } from "@/lib/backend";

export interface ActionResult {
  error?: string;
}

export async function markReachedOut(leadId: string): Promise<ActionResult> {
  const res = await backendFetch(`/api/v1/leads/${encodeURIComponent(leadId)}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ state: "REACHED_OUT" }),
  });

  if (res.status === 401) {
    redirect(`/login?expired=1&next=${encodeURIComponent(`/leads/${leadId}`)}`);
  }
  if (!res.ok) {
    return { error: await errorMessage(res) };
  }

  revalidatePath("/leads");
  revalidatePath(`/leads/${leadId}`);
  return {};
}
