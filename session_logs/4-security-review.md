# Session log 4: security review and first fixes

Representative excerpts from the Claude Code session that produced the MVP security review, issues
#8–#11, and PR #12. User prompts are quoted verbatim. Agent responses and actions are condensed, and
tool output is trimmed to the relevant lines.

- **Agent:** Claude Code (Claude Opus 5.5), running as a background job
- **Repo state at start:** `main` after PR #1 merged. By the time the fixes started, `main` had
  moved on to PR #6.

---

## 1. The ask: review, plan, and check one issue

> **User:**
> We created the initial mvp for this project, can you do a security review and propose a list of
> productionization steps?
>
> Can you also validate if this issue needs to be worked on?
> https://github.com/taylor-chen/leads-tracker/issues/2

**Agent:** Read every backend and frontend file, plus the system design doc and issue #2. It then
tested the main claims in a throwaway virtualenv instead of reasoning from the code alone:

```
1. prod with default jwt secret starts?: dev-secret-change-me
2. 73-byte hash raises: ValueError password cannot be longer than 72 bytes
4. /docs status: 200 /openapi.json: 200
5. 50MB upload -> 413 {'error': {'code': 'payload_too_large', ...}}
6. arbitrary recipient + attacker text -> 201
7. 30 bad logins, last status: 401
8. security headers: {}
```

- **Step 2** showed that `bcrypt>=4.2` installs **bcrypt 5.0**, which rejects passwords over 72
  bytes instead of truncating them. Issue #2 had left that open ("depending on the library version").
- **Step 5** showed the size limit only applies after the whole 50 MB body has been received.

`pip-audit` was clean for the backend. The frontend had no lockfile and npm wasn't installed, so the
agent web-searched the pinned versions. It found that `next@15.5.4` / `react@19.1.1` are affected by
**CVE-2025-66478 / CVE-2025-55182** (CVSS 10.0 RCE in React Server Components). The app's server
actions are exactly the affected feature.

**Answer, condensed:**

- **Critical:** the Next.js/React RCE, and no committed lockfile.
- **High:**
  - the public form lets anyone send email, with their own text, to any address
  - upload size is only checked after the full body has arrived
  - no login rate limiting
  - insecure defaults that still work in production
- **Medium:**
  - unscanned resumes
  - missing security headers and public `/docs`
  - no token revocation on logout
  - no audit trail or retention policy
  - production image issues
  - passwords passed on the command line
- **What was done well:** the path-traversal guard, file-type checks on content, the safe `?next=`
  redirect, the `httpOnly` cookie, and equal login timing.
- A 14-step productionization plan in three phases.
- **Issue #2:** every claim checked out. Two corrections:
  - Over HTTP, long passwords are handled (login returns 401). The crash only happens in the CLI.
  - The dev-secret startup check was confirmed missing.

  Recommendation: decide on SSO first, because it would make most of the password questions moot.

## 2. Triage and fixes

> **User:**
> lets create a new branch to fix the vuln issues in those packages and commit the
> package-lock.json. Also create a session log in session_logs similar to whats already there.
> Double check you are on latest main
>
> for High
> 2. That is fine for now
> 3. is there a way we can read the size first and reject early?
> 4. does fastapi come with any out of the box rate limiting?
> 5. lets create an issue for this
>
> medium
> 6. create an issue for this
> 7. fine for now
> 8. lets deactivate the token on logout
> 9. this is fine for now, lets create a feature request issue
> 10. this is fine for now
> 11. create a ticket for this

**Agent:** Ran `git fetch` first. Local `main` matched `origin/main`, but both had moved from the
reviewed commit (`3db6cb2`) to `e1022c3` (PR #6). The agent diffed the two. Only email config and
the session log names had changed, so no finding was affected. It then created a worktree from the
latest `main`.

### Dependency fix

- Looked up the latest patch releases on the current minor lines: `next@15.5.27` and
  `react`/`react-dom@19.1.9`. Stayed on 15.5.x to avoid a major upgrade.
- Generated `package-lock.json` in a `node:22-alpine` container, since Node isn't installed locally.
- `npm audit` still flagged `postcss` (bundled in `next`) and a `braces` chain (eslint tooling).
  - The agent added an npm `overrides` entry for `postcss ^8.5.29`, then rebuilt to confirm Next
    still worked with it.
  - `braces` was left as is: it's dev-only, isn't shipped in the image, and the advisory covers the
    latest release, so there's no fixed version to move to.

```
--- audit prod
found 0 vulnerabilities
typecheck ok
✔ No ESLint warnings or errors
 ✓ Compiled successfully
```

- **Caught in review:** `next build` rewrites `next-env.d.ts` to reference the gitignored
  `.next/types/routes.d.ts`. That would break `make test-frontend` on a clean checkout, so the agent
  reverted it before both commits.

### Revoking the token on logout

- Each JWT now gets a random `jti`, and tokens without one are rejected.
- New endpoint `POST /api/v1/auth/logout` stores the `jti` in a new `revoked_tokens` table
  (migration `0002`) until the token's own expiry, pruning expired rows as it goes.
- The Next.js logout route calls the endpoint, then clears the cookie whatever the result.
- The agent chose per-token revocation over a per-user `token_version`, because the ask was "this
  logout" and other devices should stay signed in. The `token_version` idea stays in #2 for password
  changes.
- **Tests:** 5 new tests, 32 passing in total.
- **End-to-end check on Postgres:** the user's own stack already held the default ports, so the
  agent started a second compose project on remapped ports instead of touching it:

```
login: 200
leads page: 200
api /me before: 200
logout: 303 -> http://0.0.0.0:3000/login
api /me with copied token after logout: {"error":{"code":"not_authenticated",...}} 401
leads page with replayed cookie: 307 -> /login?expired=1&next=%2Fleads
```

A manually inserted expired `revoked_tokens` row was deleted on the next logout. The agent noted
(without fixing) a pre-existing quirk: the logout redirect points at the container's bind address
`0.0.0.0:3000`.

### Answers that didn't need code

- **Rejecting oversized uploads early (High 3):** yes. Check `Content-Length` before reading the body:
  - in the Next.js route, before `request.formData()`
  - in FastAPI, in a small middleware or ASGI wrapper
  - at the ingress (`client_max_body_size` / a WAF body-size rule)

  Clients can omit the header (chunked uploads), so the fallback is to count bytes while streaming
  and abort past the limit. The proxy limit is the real backstop.
- **Rate limiting (High 4):** FastAPI and Starlette have none built in. The options are:
  - `slowapi` (a decorator-based port of Flask-Limiter, with Redis-backed counters for multiple
    replicas)
  - `fastapi-limiter` (Redis)
  - rate limiting at the gateway/WAF, which is preferable in production

### Issues

- **#8:** refuse insecure defaults in production
- **#9:** scan resumes for malware
- **#10:** feature request for audit trail, access control and retention
- **#11:** stop passing passwords on the command line

The agent wrote them in the same structure as #2 (current behaviour, proposed checklist) and edited
#8 to link #11 once that number existed.

**Draft PR #12** has both commits and this log.

## 3. Is a 5k-line lockfile normal?

> **User:** The frontend/package-lock.json is much bigger than i had anticipated, is it normal that
> its 5k LoC long?

**Agent:** Counted the packages in the lockfile instead of answering from general knowledge:

```
5581 package-lock.json
packages: 364 dev-only: 310 prod: 54 (of which optional platform binaries: 38 )
eslint-config-next      292 packages
eslint                   85 packages
next                     53 packages
```

**Answer:** yes, and it's small for a Next.js app.

- Each entry is about 14 lines: version, URL, integrity hash and dependencies.
- 310 of the 364 packages are lint tooling, mostly from `eslint-config-next`.
- Only 54 are production packages, and 38 of those are per-platform binaries where npm installs just
  the one matching the machine.
- The lockfile only records what `package.json` already declared; it doesn't add dependencies.

The agent advised against trimming the lint setup just to shrink the file. Nothing changed.

## 4. Syncing with `main`

> **User:** okay, actually there was a change in main for github CI and a new Cluade.md file, can
> you get the latest changes?

**Agent:** Fetched `origin/main` and found one new commit, PR #7. It added GitHub Actions CI, a new
`CLAUDE.md` with session-log rules, and `session_logs/3-github-actions-ci.md`. Then:

- **Merged rather than rebased,** because the branch already had an open PR and a rebase would need
  a force-push.
- **Renumbered this log from 3 to 4.** The new `CLAUDE.md` says to take one more than the highest
  number across `main` and open PR branches, and `main` now had a log 3. PR #12 was the only open PR.
- **Followed the "one log per session" rule** by updating this file rather than starting a new one.
- **Switched the CI frontend job to `npm ci`**, with npm caching keyed on the lockfile. The workflow
  used `npm install` because `main` had no lockfile when it was written. With this PR's lockfile,
  `npm ci` installs exactly the locked versions and fails if the lockfile and `package.json`
  disagree.
- **Checked the log against the redaction rule.** The only secret-like string is
  `dev-secret-change-me`, the public placeholder in `config.py` that the finding is about.

---

## Takeaways

- **Test claims before reporting them.** A quick script turned "probably" into numbers: the default
  secret accepted in production, the bcrypt 5 behaviour, uploads received in full before the 413.
  It also corrected one detail in the issue being reviewed.
- **Re-check the base before branching.** `main` moved during the session. Diffing it against the
  reviewed commit showed the findings still held.
- **Don't take over shared resources.** The user's running stack held the ports, so verification
  ran as a separate compose project on other ports and was torn down afterwards.
- **Watch for build side effects.** `next build` silently edited a tracked file in a way that would
  break CI on a clean checkout.
