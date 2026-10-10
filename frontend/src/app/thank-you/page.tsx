import Link from "next/link";

/** Shown after a lead is submitted. */
export default function ThankYouPage() {
  return (
    <main className="container narrow">
      <section className="card center">
        <h1>Thank you!</h1>
        <p>
          We&apos;ve received your submission and sent a confirmation to your email. An attorney
          will be in touch soon.
        </p>
        <Link href="/" className="button secondary">
          Submit another
        </Link>
      </section>
    </main>
  );
}
