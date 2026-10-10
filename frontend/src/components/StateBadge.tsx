import { LEAD_STATE_LABELS, type LeadState } from "@/lib/types";

export function StateBadge({ state }: { state: LeadState }) {
  return <span className={`badge badge-${state.toLowerCase()}`}>{LEAD_STATE_LABELS[state]}</span>;
}
