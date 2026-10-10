import { LoginForm } from "@/components/LoginForm";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; expired?: string }>;
}) {
  const { next, expired } = await searchParams;
  return (
    <main className="container narrow">
      <header className="page-header">
        <h1>Attorney sign in</h1>
      </header>
      <section className="card">
        {expired && <p className="notice">Your session has expired. Please sign in again.</p>}
        <LoginForm next={next} />
      </section>
    </main>
  );
}
