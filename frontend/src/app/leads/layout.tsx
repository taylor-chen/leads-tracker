import Link from "next/link";

import { backendJsonOrLogin } from "@/lib/backend";
import type { UserSummary } from "@/lib/types";

/** Shell for the attorney dashboard. Loading the current user also enforces sign-in. */
export default async function LeadsLayout({ children }: { children: React.ReactNode }) {
  const me = await backendJsonOrLogin<UserSummary>("/api/v1/auth/me", "/leads");

  return (
    <>
      <nav className="topbar">
        <Link href="/leads" className="brand">
          Leads Tracker
        </Link>
        <div className="topbar-right">
          <span className="muted">{me.full_name}</span>
          <Link href="/leads/account">Account</Link>
          <form action="/api/auth/logout" method="post">
            <button type="submit" className="link-button">
              Sign out
            </button>
          </form>
        </div>
      </nav>
      <main className="container">{children}</main>
    </>
  );
}
