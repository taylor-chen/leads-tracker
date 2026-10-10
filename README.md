# leads-tracker

Collects leads from a **public** form (first name, last name, email, resume/CV), emails both the
prospect and an attorney on submission, and gives attorneys an **authenticated** dashboard to review
leads and mark them `PENDING → REACHED_OUT`.

- **Backend:** FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL · SMTP email
- **Frontend:** Next.js 15 (App Router, TypeScript)
- **Local infra:** Docker Compose (Postgres, Mailpit for email, backend, frontend)

See [`docs/system-design.md`](docs/system-design.md) for the architecture, data model, API and trade-offs.

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2), running.
- `make` (preinstalled on macOS/Linux).

Nothing else is needed on the host. Python and Node run inside containers.

## Run it

```bash
make up          # build and start everything in the background
make logs        # follow logs (Ctrl-C to stop following); SERVICE=backend for one service
```

Run `make` on its own to list every command.

The first build takes a few minutes. Once it's up:

| What | URL |
|---|---|
| Public lead form | http://localhost:3000 |
| Attorney dashboard | http://localhost:3000/leads |
| Email inbox (Mailpit) | http://localhost:8025 |
| API docs (Swagger) | http://localhost:8000/docs |

On startup the backend runs DB migrations and creates a default attorney login:

- **Email:** `attorney@example.com`
- **Password:** `changeme123`

To change these or the notification recipient, copy `.env.example` to `.env` and edit it before
`make up`. The same file holds the SMTP settings: they default to Mailpit, and `.env.example`
shows how to point them at a real provider (Resend) to send real email.

### Stop it

```bash
make down        # stop containers, keep data
make reset       # stop and delete all data (database + uploaded resumes)
```

### Other commands

```bash
make ps          # service status
make create-user EMAIL=jane@example.com PASSWORD=a-strong-pw NAME="Jane Doe"   # add an attorney
```

## Manual E2E walkthrough

1. Open http://localhost:3000 and submit the form with a PDF/DOC/DOCX resume (≤ 5 MB).
2. Open Mailpit at http://localhost:8025. You should see two emails: a confirmation to the
   prospect and a "New lead" notification to `attorney@example.com`, which links to the lead.
3. Go to http://localhost:3000/leads. You'll be redirected to sign in. Use the credentials above.
4. The lead is listed as **Pending**. Click the resume link to download it, and click the name to
   see the detail page.
5. Click **Mark reached out**. The state becomes **Reached out** and records who did it and when.
   Use the filter tabs to view by state.

The same flow via the API:

```bash
curl -F first_name=Ada -F last_name=Lovelace -F email=ada@example.com \
     -F resume=@/path/to/resume.pdf http://localhost:8000/api/v1/leads

TOKEN=$(curl -s -H 'content-type: application/json' \
  -d '{"email":"attorney@example.com","password":"changeme123"}' \
  http://localhost:8000/api/v1/auth/login | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/leads
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' \
     -d '{"state":"REACHED_OUT"}' http://localhost:8000/api/v1/leads/<lead-id>
```

## Running the tests

```bash
make test            # everything below
make test-backend    # pytest (in-memory SQLite + captured email outbox; stack needn't be running)
make test-frontend   # TypeScript type-check + ESLint in a throwaway Node container
make lint            # ruff (backend) + ESLint (frontend)
```

The frontend image also type-checks during `next build`, so `make up` fails on type errors.

The same checks run in GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) on
every pull request and on pushes to `main`.

### Without Docker (optional)

```bash
# Backend: Python 3.12+
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest

# Frontend: Node 22+
cd frontend
npm install
npm run typecheck && npm run lint
API_URL=http://localhost:8000 npm run dev
```
