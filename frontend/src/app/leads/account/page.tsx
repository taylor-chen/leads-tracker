import Link from "next/link";

import { ChangePasswordForm } from "@/components/ChangePasswordForm";

/** Account settings for the signed-in attorney. Currently just password change. */
export default function AccountPage() {
  return (
    <div className="narrow-section">
      <p>
        <Link href="/leads">← All leads</Link>
      </p>
      <header className="page-header">
        <h1>Account</h1>
      </header>
      <section className="card">
        <h2>Change password</h2>
        <p className="muted">You&apos;ll be signed out everywhere and asked to sign in again.</p>
        <ChangePasswordForm />
      </section>
    </div>
  );
}
