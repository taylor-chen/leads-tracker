"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

const MAX_RESUME_BYTES = 5 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx"];

function validateResume(file: File | null): string | null {
  if (!file || file.size === 0) return "Please attach your resume.";
  const name = file.name.toLowerCase();
  if (!ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext))) {
    return "Resume must be a PDF, DOC or DOCX file.";
  }
  if (file.size > MAX_RESUME_BYTES) return "Resume must be 5 MB or smaller.";
  return null;
}

export function LeadForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const form = new FormData(event.currentTarget);
    const resumeError = validateResume(form.get("resume") as File | null);
    if (resumeError) {
      setError(resumeError);
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/leads", { method: "POST", body: form });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setError(body?.error?.message ?? "Something went wrong. Please try again.");
        return;
      }
      router.push("/thank-you");
    } catch {
      setError("Network error. Please check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="form" noValidate={false}>
      <div className="form-row">
        <label>
          First name
          <input name="first_name" required maxLength={100} autoComplete="given-name" />
        </label>
        <label>
          Last name
          <input name="last_name" required maxLength={100} autoComplete="family-name" />
        </label>
      </div>
      <label>
        Email
        <input name="email" type="email" required maxLength={320} autoComplete="email" />
      </label>
      <label>
        Resume / CV
        <input
          name="resume"
          type="file"
          required
          accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        />
        <span className="hint">PDF, DOC or DOCX · up to 5 MB</span>
      </label>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <button type="submit" disabled={submitting}>
        {submitting ? "Submitting…" : "Submit"}
      </button>
    </form>
  );
}
