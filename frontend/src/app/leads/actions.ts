"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { loginPath } from "@/lib/auth";
import { backendFetch, errorMessage } from "@/lib/backend";
import type { ActionResult } from "@/lib/types";

/** Server action: move a lead to REACHED_OUT and refresh the pages that show it. */
export async function markReachedOut(leadId: string): Promise<ActionResult> {
  const res = await backendFetch(`/api/v1/leads/${encodeURIComponent(leadId)}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ state: "REACHED_OUT" }),
  });

  if (res.status === 401) {
    redirect(loginPath(`/leads/${leadId}`, { expired: true }));
  }
  if (!res.ok) {
    return { error: await errorMessage(res) };
  }

  revalidatePath("/leads");
  revalidatePath(`/leads/${leadId}`);
  return {};
}
