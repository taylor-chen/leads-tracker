# CLAUDE.md

## Session logs

Every session that commits a change must also commit a session log to `session_logs/`.

- **When:** with the session's first commit. Commit the log alongside the change, or as the next
  commit on the same branch, so it lands in the same PR.
- **One log per session:** if the session commits again later, update its existing log with what
  changed. Don't start a new file.
- **Name:** `session_logs/<n>-<short-kebab-topic>.md`, where `<n>` is one more than the highest
  existing number. Check `main` and any open PR branches so numbers don't collide.
- **Format:** follow the existing logs (see `session_logs/2-email-provider.md`):
  - `# Session log <n>: <topic>` title, then a short intro naming the PR/issue it produced and
    stating that user prompts are verbatim, agent actions are condensed and tool output is trimmed
  - bullets for **Agent** (model, how it ran) and **Repo state at start**
  - `---`, then numbered `##` sections, one per user turn or notable moment: the user's prompt as
    a `> **User:**` blockquote, then a condensed **Agent:** account of what it read, decided, changed
    and verified, with short trimmed tool-output snippets where they matter
  - be honest about gaps: what wasn't verified, what was blocked, and where the agent pushed back
  - a closing `## Takeaways` section with 2–4 bullets
- **Redact:** no secrets, tokens, `.env` values or personal data in quoted prompts or output.
