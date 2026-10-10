"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { backendFetch } from "@/lib/backend";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";
import type { ActionResult } from "@/lib/types";

/**
 * Server action for ChangePasswordForm. On success the API has signed out every session,
 * so this clears the cookie and sends the user to sign in with the new password.
 */
export async function changePassword(_prev: ActionResult, form: FormData): Promise<ActionResult> {
  const currentPassword = String(form.get("current_password") ?? "");
  const newPassword = String(form.get("new_password") ?? "");
  if (!currentPassword || !newPassword) {
    return { error: "All fields are required" };
  }
  if (newPassword !== String(form.get("confirm_password") ?? "")) {
    return { error: "New passwords don't match" };
  }

  const res = await backendFetch("/api/v1/auth/change-password", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const error: { code?: string; message?: string } | undefined = body?.error;
    // A wrong current password is also a 401; only a missing/expired session goes to login.
    if (res.status === 401 && error?.code !== "invalid_current_password") {
      redirect(`/login?expired=1&next=${encodeURIComponent("/leads/account")}`);
    }
    return { error: error?.message ?? "Could not change password" };
  }

  // The API has invalidated every session, including this one, so sign out here too.
  (await cookies()).set(SESSION_COOKIE, "", { ...sessionCookieOptions, maxAge: 0 });
  redirect("/login?password_changed=1");
}
