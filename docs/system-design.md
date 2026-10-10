# Leads Tracker: System Design

## 1. Requirements

**Functional**
- A public form collects a lead: first name, last name, email, and resume/CV (all required).
- When a lead is submitted, email the prospect (a confirmation) and an internal attorney (a notification).
- An internal UI, behind auth, lists leads with everything the prospect submitted.
- Each lead has a state: it starts as `PENDING` and an attorney manually moves it to `REACHED_OUT`.
- The API supports creating, getting (one or many) and updating leads.

**Non-functional**
- The public endpoint must tolerate untrusted input: validate fields, file type and size, and never trust filenames.
- PII (names, emails, resumes) is visible only to authenticated attorneys.
- A slow or failing email provider must not cause submissions to fail.
- Production-style structure: layered code, migrations, config via env, tests, containerised.

## 2. Architecture

```
                ┌──────────────────────────────── docker compose ────────────────────────────────┐
                │                                                                                 │
 Prospect ──►   │  Next.js (frontend:3000)                    FastAPI (backend:8000)              │
 Attorney ──►   │   • pages: /, /login, /leads, /leads/[id]    • /api/v1/leads, /api/v1/auth       │
                │   • route handlers / server actions ──HTTP──►• service layer ──► Postgres        │
                │   • session = httpOnly cookie (JWT)          │                ──► uploads volume  │
                │                                              └─ background task ─SMTP─► Mailpit   │
                └─────────────────────────────────────────────────────────────────────────────────┘
```

- **Browser → Next.js only.** The browser never calls FastAPI directly. Next.js route handlers and
  server actions call the API server-to-server, so:
  - the API JWT lives in an `httpOnly`, `SameSite=Lax` cookie and is never readable by JS (XSS can't steal it);
  - the API doesn't need to be publicly exposed and CORS stays trivial.
- **FastAPI** is the system of record. Its layers are routers (HTTP), services (business rules),
  repositories (SQL), and adapters (email, file storage).
- **Postgres** stores leads and users. **Alembic** manages the schema.
- **Resume files** are stored behind a `StorageBackend` interface. Locally that's a Docker volume;
  in production it's a drop-in S3/GCS implementation with private buckets.
- **Email** goes through an `EmailSender` interface. `SmtpEmailSender` works with Mailpit locally
  and with SES, SendGrid or Postmark SMTP in production. `ConsoleEmailSender` is used in tests.

### Submission flow

1. The prospect submits multipart form data to `POST /api/leads` (Next.js), which forwards it to
   `POST /api/v1/leads`.
2. FastAPI validates the fields (Pydantic, `EmailStr`) and the resume: allowed extension, matching
   file signature (magic bytes), non-empty, ≤ 5 MB.
3. The file is saved under a server-generated key. The lead row is inserted as `PENDING`. If the DB
   write fails, the file is deleted.
4. The response is `201` with only `{id, created_at}`, so no PII is echoed back.
5. After the response, a `BackgroundTask` sends both emails. Each send is independent; failures are
   logged and don't affect the prospect.

### Attorney flow

1. `/leads/*` is guarded by Next.js middleware (no cookie → `/login?next=…`).
2. Login: `POST /api/auth/login` (Next.js) → `POST /api/v1/auth/login` → JWT → `httpOnly` cookie.
3. Pages fetch `GET /api/v1/leads` / `GET /api/v1/leads/{id}` with a bearer token. A `401` (an
   expired token) redirects to login.
4. "Mark reached out" is a server action → `PATCH /api/v1/leads/{id} {state: REACHED_OUT}` →
   revalidates the page.
5. Resume download is proxied through `GET /api/leads/{id}/resume` and streamed from the API.
6. Sign out: `POST /api/auth/logout` (Next.js) → `POST /api/v1/auth/logout` revokes the token, then
   the cookie is cleared (even if the API call fails).

## 3. Data model

```
users                                   leads
─────                                   ─────
id               uuid PK                id                   uuid PK
email            varchar unique         first_name           varchar(100)
hashed_password  varchar (bcrypt)       last_name            varchar(100)
full_name        varchar                email                varchar(320)  idx
is_active        bool                   resume_key           varchar  (storage key, server-generated)
created_at       timestamptz            resume_filename      varchar  (sanitised original name)
updated_at       timestamptz            resume_content_type  varchar
                                        resume_size_bytes    int
                                        state                enum lead_state(PENDING, REACHED_OUT) idx
                                        reached_out_at       timestamptz null
                                        reached_out_by_id    uuid FK users.id null
                                        created_at           timestamptz idx
                                        updated_at           timestamptz

revoked_tokens
──────────────
jti              varchar PK
expires_at       timestamptz idx  (rows are pruned once past this)
revoked_at       timestamptz
```

The state machine is data (`LEAD_STATE_TRANSITIONS`): `PENDING → REACHED_OUT`, and `REACHED_OUT`
is terminal. Other transitions return `409`. Setting the current state again is a no-op `200`
(idempotent). Adding a state such as `RETAINED` means one enum value, one transition entry, and a
migration.

## 4. API (`/api/v1`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/leads` | public | Create a lead (multipart: `first_name`, `last_name`, `email`, `resume`). `201 {id, created_at}` |
| `GET` | `/leads?state=&page=&page_size=` | bearer | Paginated list, newest first, optional state filter |
| `GET` | `/leads/{id}` | bearer | Lead detail |
| `PATCH` | `/leads/{id}` | bearer | Update the lead's state (`{"state": "REACHED_OUT"}`) |
| `GET` | `/leads/{id}/resume` | bearer | Download the resume |
| `POST` | `/auth/login` | public | `{email, password}` → `{access_token, expires_in}` |
| `POST` | `/auth/logout` | bearer | Revoke the current token. `204` |
| `GET` | `/auth/me` | bearer | Current user |
| `GET` | `/health` | public | Liveness |

Errors use one envelope: `{"error": {"code": "...", "message": "..."}}`. Status codes: `401` not
authenticated, `404` not found, `409` invalid state transition, `413` file too large, `422`
validation error.

## 5. Security

- **Auth:** bcrypt password hashes and HS256 JWTs (8 h). Login runs a constant-time-ish dummy check
  for unknown emails. Inactive users are rejected.
- **Logout:** each JWT carries a random `jti`. Logout stores it in `revoked_tokens` until the token
  would have expired, and every authenticated request checks that table, so a copied token stops
  working once its session signs out. Other sessions of the same user stay signed in.
- **Session:** the JWT lives in an `httpOnly` cookie (set `COOKIE_SECURE=true` behind HTTPS).
  `SameSite=Lax` plus the server actions' built-in origin checks mitigate CSRF. `?next=` redirects
  are restricted to relative paths.
- **Uploads:** an extension allow-list plus a magic-byte check and a size cap. Storage keys are
  random UUIDs, so user-supplied filenames never reach the filesystem path, and path traversal is
  guarded in `LocalStorage.path_for`. Downloads are served with `Content-Disposition: attachment`.
- **PII exposure:** the public endpoint returns only an id, and every read endpoint requires auth.

## 6. Production considerations / next steps

| Area | Current (this repo) | Production |
|---|---|---|
| Email delivery | FastAPI `BackgroundTasks` (in-process) | Durable queue (SQS/Celery/RQ) or a transactional outbox table with retries and a dead-letter queue |
| File storage | Docker volume | S3 with SSE, private bucket, presigned download URLs. Optional antivirus scan (e.g. ClamAV Lambda) before marking a lead visible |
| Abuse | Size/type validation | Rate limiting per IP (gateway/WAF), CAPTCHA (Turnstile/reCAPTCHA) on the public form |
| Auth | Local users + JWT | SSO (OIDC with Google Workspace/Okta) for attorneys, short-lived tokens with refresh, role-based permissions |
| Attorney routing | Single configured inbox | Assignment rules / round-robin, `assigned_to` on leads |
| Audit | `reached_out_by/at` | `lead_events` table for a full history of state changes |
| Observability | Structured logs | Request IDs, OpenTelemetry tracing, Sentry, metrics on submissions and email failures |
| Deploy | docker compose | Containers on ECS/Kubernetes/Cloud Run, managed Postgres (RDS), Vercel or a container for Next.js, migrations as a release step |
| Data | Indexes on state/created_at/email | Retention policy for resumes, GDPR export/delete endpoints |
