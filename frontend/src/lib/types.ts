// Mirrors the API's response schemas in backend/app/schemas.

export type LeadState = "PENDING" | "REACHED_OUT";

export const LEAD_STATES: LeadState[] = ["PENDING", "REACHED_OUT"];

export const LEAD_STATE_LABELS: Record<LeadState, string> = {
  PENDING: "Pending",
  REACHED_OUT: "Reached out",
};

export interface UserSummary {
  id: string;
  full_name: string;
  email: string;
}

export interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  resume: {
    filename: string;
    content_type: string;
    size_bytes: number;
  };
  state: LeadState;
  reached_out_at: string | null;
  reached_out_by: UserSummary | null;
  created_at: string;
  updated_at: string;
}

export interface LeadPage {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
}

/** Return value of a server action used with `useActionState`: empty on success. */
export interface ActionResult {
  error?: string;
}

/** Narrow an untrusted value (e.g. a query param) to a `LeadState`. */
export function isLeadState(value: unknown): value is LeadState {
  return typeof value === "string" && (LEAD_STATES as string[]).includes(value);
}
