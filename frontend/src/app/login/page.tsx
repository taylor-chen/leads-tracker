import { LoginForm } from "@/components/LoginForm";

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
