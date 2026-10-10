import Link from "next/link";
import { notFound } from "next/navigation";

import { MarkReachedOutButton } from "@/components/MarkReachedOutButton";
import { StateBadge } from "@/components/StateBadge";
import { ApiError, backendJsonOrLogin } from "@/lib/backend";
import { formatBytes, formatDateTime } from "@/lib/format";
import type { Lead } from "@/lib/types";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Fetch a lead, showing the 404 page for a malformed or unknown id. */
async function loadLead(id: string): Promise<Lead> {
  if (!UUID_RE.test(id)) notFound();
  try {
    return await backendJsonOrLogin<Lead>(`/api/v1/leads/${id}`, `/leads/${id}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }
}

export default async function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const lead = await loadLead(id);
  const name = `${lead.first_name} ${lead.last_name}`;

  return (
    <>
      <p>
        <Link href="/leads">← All leads</Link>
      </p>
      <header className="page-header row">
        <h1>{name}</h1>
        <StateBadge state={lead.state} />
      </header>

      <section className="card">
        <dl className="details">
          <dt>First name</dt>
          <dd>{lead.first_name}</dd>
          <dt>Last name</dt>
          <dd>{lead.last_name}</dd>
          <dt>Email</dt>
          <dd>
            <a href={`mailto:${lead.email}`}>{lead.email}</a>
          </dd>
          <dt>Resume</dt>
          <dd>
            <a href={`/api/leads/${lead.id}/resume`}>{lead.resume.filename}</a>{" "}
            <span className="muted">({formatBytes(lead.resume.size_bytes)})</span>
          </dd>
          <dt>Submitted</dt>
          <dd>{formatDateTime(lead.created_at)}</dd>
          <dt>State</dt>
          <dd>
            <StateBadge state={lead.state} />
          </dd>
          {lead.state === "REACHED_OUT" && (
            <>
              <dt>Reached out</dt>
              <dd>
                {formatDateTime(lead.reached_out_at)}
                {lead.reached_out_by && ` by ${lead.reached_out_by.full_name}`}
              </dd>
            </>
          )}
        </dl>

        {lead.state === "PENDING" && (
          <div className="card-actions">
            <MarkReachedOutButton leadId={lead.id} leadName={name} />
          </div>
        )}
      </section>
    </>
  );
}
