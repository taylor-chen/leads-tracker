# Session log 7: logout redirecting to `0.0.0.0:10000`

Representative excerpts from the Claude Code session that fixed a production bug where signing out
sent the browser to `https://0.0.0.0:10000/login`, and opened the draft PR for it. User prompts are
quoted verbatim. Agent responses and actions are condensed, and tool output is trimmed to the
relevant lines.

- **Agent:** Claude Code (Claude Opus 5.5), running as a background job in an isolated worktree
- **Repo state at start:** `main` at PR #13 (change password). The frontend runs as the Next.js
  standalone server in Docker (`HOSTNAME=0.0.0.0`, `PORT` from the host).

---

## 1. The report

> **User:** i noticed a bug in production, when i signout, it looks hardcoded to go to
> https://0.0.0.0:10000/login which isn't right

**Agent:** Grepped for `/login` redirects. The logout route handler built its target with
`NextResponse.redirect(new URL("/login", request.url), 303)`. In the standalone server a route
handler's `request.url` is assembled from the server's own bind address (`HOSTNAME`/`PORT`), not
the public host behind the proxy. That produces `0.0.0.0:10000`. Two other places used the same
pattern: `middleware.ts` and the resume download route's 401 branch.

Fix: a small `redirectToPath()` helper in `frontend/src/lib/redirect.ts` returns a response with a
**relative** `Location` header. The browser resolves it against the URL it actually requested, so
no host header or `PUBLIC_URL` setting has to be trusted or configured.

## 2. Verifying without local Node

No Node toolchain was installed on the machine, so everything ran in Docker on `node:22-alpine`, the
image CI and production use. `npm run typecheck` and `npm run lint` both passed. The agent built
production images from `main` and from the fix, ran each with `PORT=10000`, and curled them:

```
main  POST /api/auth/logout        303  location: http://0.0.0.0:10000/login
fix   POST /api/auth/logout        303  location: /login   (session cookie still cleared)
main  GET  /api/leads/abc/resume   307  location: http://0.0.0.0:10000/login?expired=1&next=%2Fleads%2Fabc
fix   GET  /api/leads/abc/resume   307  location: /login?expired=1&next=%2Fleads%2Fabc
```

A throwaway Python stub returning 401 stood in for the API, so the resume route's expired-session
branch and logout's revocation call actually ran.

## 3. Middleware: a change reverted

The first version also switched `middleware.ts` to the helper. That returned a **500**
(`TypeError: Invalid URL, input: '/login?next=…'`): the middleware runtime requires an absolute
`Location`. The `main` image showed middleware was never affected, because Next rewrites
same-origin middleware redirects to relative ones (`location: /login?next=%2Fleads%2Fabc%3Fx%3D1`).
The agent reverted the middleware change and noted in the helper's doc that it is for route
handlers only.

Not verified: the fix wasn't tested against the real production proxy, only by reproducing the
standalone server's behaviour locally with the same port.

## Takeaways

- In a standalone Next.js deployment behind a proxy, don't build redirect URLs from `request.url`
  in route handlers. Use a relative `Location`.
- Server-action `redirect()` and middleware redirects were already relative and needed no change.
- Building the real production image and diffing response headers against `main` caught both the
  second instance of the bug and the middleware regression the first fix would have caused.
