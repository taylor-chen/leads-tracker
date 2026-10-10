"use client";

import { useState, useTransition } from "react";

import { markReachedOut } from "@/app/leads/actions";

/** Asks for confirmation, then marks the lead REACHED_OUT, showing any error inline. */
export function MarkReachedOutButton({ leadId, leadName }: { leadId: string; leadName: string }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function handleClick() {
    if (!window.confirm(`Mark ${leadName} as reached out? This can't be undone.`)) return;
    setError(null);
    startTransition(async () => {
      const result = await markReachedOut(leadId);
      if (result.error) setError(result.error);
    });
  }

  return (
    <span>
      <button type="button" className="small" onClick={handleClick} disabled={pending}>
        {pending ? "Saving…" : "Mark reached out"}
      </button>
      {error && (
        <span className="error small-text" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}
