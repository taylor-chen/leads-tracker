import Link from "next/link";

export default function NotFound() {
  return (
    <main className="container narrow">
      <section className="card center">
        <h1>Not found</h1>
        <p className="muted">The page you&apos;re looking for doesn&apos;t exist.</p>
        <Link href="/" className="button secondary">
          Go home
        </Link>
      </section>
    </main>
  );
}
