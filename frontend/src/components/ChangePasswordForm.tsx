"use client";

import { useActionState } from "react";

import { changePassword } from "@/app/leads/account/actions";

/** Change-password form backed by the `changePassword` server action. */
export function ChangePasswordForm() {
  const [state, formAction, pending] = useActionState(changePassword, {});

  return (
    <form action={formAction} className="form">
      <label>
        Current password
        <input
          name="current_password"
          type="password"
          required
          autoComplete="current-password"
        />
      </label>
      <label>
        New password
        <input
          name="new_password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
        />
        <span className="hint">At least 8 characters</span>
      </label>
      <label>
        Confirm new password
        <input
          name="confirm_password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
        />
      </label>
      {state.error && (
        <p className="error" role="alert">
          {state.error}
        </p>
      )}
      <button type="submit" disabled={pending}>
        {pending ? "Saving…" : "Change password"}
      </button>
    </form>
  );
}
