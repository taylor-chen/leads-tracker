import { LeadForm } from "@/components/LeadForm";

export default function HomePage() {
  return (
    <main className="container narrow">
      <header className="page-header">
        <h1>Get in touch</h1>
        <p className="muted">
          Tell us a bit about yourself and attach your resume. An attorney will review your
          submission and reach out to you.
        </p>
      </header>
      <section className="card">
        <LeadForm />
      </section>
    </main>
  );
}
