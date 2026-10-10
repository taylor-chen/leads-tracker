import Link from "next/link";

import { MarkReachedOutButton } from "@/components/MarkReachedOutButton";
import { StateBadge } from "@/components/StateBadge";
import { backendJsonOrLogin } from "@/lib/backend";
import { formatDateTime } from "@/lib/format";
import { LEAD_STATE_LABELS, LEAD_STATES, isLeadState, type LeadPage } from "@/lib/types";

const PAGE_SIZE = 20;

/** URL of the leads list for a filter and page, omitting defaults. */
function leadsHref(params: { state?: string; page?: number }): string {
  const qs = new URLSearchParams();
  if (params.state) qs.set("state", params.state);
  if (params.page && params.page > 1) qs.set("page", String(params.page));
  const query = qs.toString();
  return query ? `/leads?${query}` : "/leads";
}

/**
 * Attorney dashboard: paginated leads table with state filter tabs. Filter and page come
 * from the query string; an unknown state shows all leads.
 */
export default async function LeadsPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string; page?: string }>;
}) {
  const sp = await searchParams;
  const state = isLeadState(sp.state) ? sp.state : undefined;
  const page = Math.max(1, Number.parseInt(sp.page ?? "1", 10) || 1);

  const qs = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
  if (state) qs.set("state", state);
  const data = await backendJsonOrLogin<LeadPage>(
    `/api/v1/leads?${qs}`,
    leadsHref({ state, page }),
  );
  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  return (
    <>
      <header className="page-header row">
        <h1>Leads</h1>
        <nav className="tabs" aria-label="Filter by state">
          <Link href={leadsHref({})} className={!state ? "tab active" : "tab"}>
            All
          </Link>
          {LEAD_STATES.map((s) => (
            <Link key={s} href={leadsHref({ state: s })} className={state === s ? "tab active" : "tab"}>
              {LEAD_STATE_LABELS[s]}
            </Link>
          ))}
        </nav>
      </header>

      {data.items.length === 0 ? (
        <p className="card muted center">No leads yet.</p>
      ) : (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Resume</th>
                <th>Submitted</th>
                <th>State</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {data.items.map((lead) => {
                const name = `${lead.first_name} ${lead.last_name}`;
                return (
                  <tr key={lead.id}>
                    <td>
                      <Link href={`/leads/${lead.id}`}>{name}</Link>
                    </td>
                    <td>
                      <a href={`mailto:${lead.email}`}>{lead.email}</a>
                    </td>
                    <td>
                      <a href={`/api/leads/${lead.id}/resume`}>{lead.resume.filename}</a>
                    </td>
                    <td>{formatDateTime(lead.created_at)}</td>
                    <td>
                      <StateBadge state={lead.state} />
                    </td>
                    <td className="actions">
                      {lead.state === "PENDING" && (
                        <MarkReachedOutButton leadId={lead.id} leadName={name} />
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <footer className="pagination">
        <span className="muted">
          {data.total} lead{data.total === 1 ? "" : "s"} · page {page} of {totalPages}
        </span>
        <span>
          {page > 1 && (
            <Link href={leadsHref({ state, page: page - 1 })} className="button secondary small">
              Previous
            </Link>
          )}
          {page < totalPages && (
            <Link href={leadsHref({ state, page: page + 1 })} className="button secondary small">
              Next
            </Link>
          )}
        </span>
      </footer>
    </>
  );
}
