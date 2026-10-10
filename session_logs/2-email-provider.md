# Session log 2: choosing a real email provider

Representative excerpts from the Claude Code session that produced issue #5 and PR #6. User prompts
are quoted verbatim. Agent responses and actions are condensed, and tool output is trimmed to the
relevant lines.

- **Agent:** Claude Code (Claude Opus 5.5), running as a background job
- **Repo state at start:** `main` after PR #1 merged. Email went only to Mailpit.

---

## 1. The ask: research, don't build yet

> **User:**
> Currently in the repo we have a local way to test out the emailing, I want to be able to send out
> a real email as a test and as a way forward towards productionization, can you do a quick research
> of which public 3rd party we can use then we can decide a way to implement it later

**Agent:** Read the email code before searching. That shaped the whole answer:

- `SmtpEmailSender` already works with any SMTP relay, and all the candidate providers offer one.
  So a real send needs config, not code.
- The one catch was that `docker-compose.yml` hardcoded the Mailpit host and port:

```yaml
      EMAIL_BACKEND: smtp
      SMTP_HOST: mailpit
      SMTP_PORT: 1025
```

## 2. Research

**Agent:** Ran four web searches in parallel, one each for Resend, Postmark and Amazon SES, plus one
covering SendGrid, Brevo and Mailgun. The sources were 2026 third-party pricing roundups, and some
disagreed with each other. The agent kept the conflicts visible instead of picking a number:

| Provider | Free tier | Paid entry | Finding |
|---|---|---|---|
| Resend | 3,000/mo, max 100/day | $20/mo for 50k | Consistent across sources |
| Postmark | 100/mo | ~$15/mo for 10k | Best transactional deliverability |
| Amazon SES | Unclear (credits vs allowance) | ~$0.10 per 1k | Sources conflicted; the reported July 2026 plan restructure couldn't be confirmed |
| SendGrid | None | $19.95/mo | Free plan ended May 2025 |
| Mailgun | Unclear | ~$15/mo | Sources conflicted |

**Recommendation:**

- **Resend** for the first real send.
- **Postmark** for production if deliverability matters most. These are confirmation emails to a
  legal team's prospects.
- **SES** if the app is hosted on AWS and volume grows.

The agent also listed prerequisites that apply to any provider:

- a verified sending domain with SPF, DKIM and DMARC records (`leads.local` won't work)
- sandbox limits on first sends
- a durable queue before real prospect traffic

It changed no files, because the user wanted to decide later.

## 3. Turning research into work

> **User:** lets make the change to move the value from docker compose to .env, you can make that
> change. Can you also create a gh issue suggesting resend + instructions on how to make the switch,
> can also add a note in the ticket to investigate a multi-vendor system where we can use resend and
> postmark? It would reduce our reliance and lockin on 1 vendor, and we can utilize both their free
> tiers

**Agent:** Created an isolated worktree, then made three changes:

- **`docker-compose.yml`:** all seven SMTP settings now read from `.env`, with Mailpit as the
  default, e.g. `SMTP_HOST: ${SMTP_HOST:-mailpit}`.
- **`.env.example`:** documents the settings and includes a commented Resend block (`smtp.resend.com`,
  port 465 with SSL, username `resend`, API key as the password).
- **README:** one sentence pointing to `.env.example`.

**Verification:** `docker compose config` resolved to the same Mailpit values both without a `.env`
and with `.env.example` copied in. The sandbox blocked a container-based check of the backend's
`Settings` parsing. Instead, the agent reasoned it through from the code: Pydantic reads `"false"`
as `False`, and `SmtpEmailSender` only logs in when both credentials are truthy, so empty strings
leave the Mailpit path unchanged. The PR description states the gap: no `make up` and no real send
were run.

**Issue #5** has three parts:

- **Why Resend:** the rationale plus the alternatives table.
- **How to switch:**
  1. Verify the domain.
  2. Create an API key.
  3. Fill in the `.env` values.
  4. Submit the form and check delivery in the Resend dashboard.
  5. Keep the key out of git.
- **Investigate multi-vendor:** a `FailoverEmailSender` that wraps an ordered list of senders and
  fits the existing `EmailSender` interface. The open questions were:
  - shared domain setup (a DKIM selector for each vendor, and SPF's 10-lookup limit)
  - idempotent retries
  - keeping bounce and suppression lists in sync across vendors
  - slower reputation building when volume is split
  - each vendor's free-tier terms

**Agent added one honest caveat** to the user's free-tier argument. Postmark's free tier is only
100 emails a month, so most of the value of multi-vendor is resilience and less lock-in, not extra
capacity.

**Draft PR #6** links to the issue.

## 4. This log

> **User:** could you also create a Representative prompt logs or session transcripts (excerpts are
> fine) in sessions_logs similar to the one in there already for this session? Can you also number
> the existing one to 1 and the new log to 2?

**Agent:** Renamed `claude-code-session.md` to `1-leads-app-build.md` and wrote this file on the
same branch, so both are in PR #6.

---

## Takeaways

- **Read the code before researching.** The existing SMTP adapter turned "which provider?" into a
  config change, and showed that the hardcoded compose values were the only blocker.
- **Report source conflicts as they are.** Pricing roundups disagreed on SES and Mailgun. The
  answer flagged this and pointed to vendor pages instead of picking a number.
- **Push back on the reasoning, not the request.** The multi-vendor idea went into the issue as
  asked, with its trade-offs: tiny Postmark free tier, DNS setup, suppression sync.
