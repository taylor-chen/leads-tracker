import { LoginForm } from "@/components/LoginForm";

/** Attorney sign-in. `?next=` is where to go after; the other params pick a notice. */
export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; expired?: string; password_changed?: string }>;
}) {
  const { next, expired, password_changed } = await searchParams;
  return (
    <main className="container narrow">
      <header className="page-header">
        <h1>Attorney sign in</h1>
      </header>
      <section className="card">
        {password_changed ? (
          <p className="notice">Your password has been changed. Please sign in again.</p>
        ) : (
          expired && <p className="notice">Your session has expired. Please sign in again.</p>
        )}
        <LoginForm next={next} />
      </section>
    </main>
  );
}
