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

Nothing else is needed on the host. Python and Node run inside containers.

## Run it

```bash
docker compose up --build        # add -d to run in the background
```

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
`docker compose up`.

### Stop it

```bash
docker compose down              # stop containers, keep data
docker compose down -v           # stop and delete all data (database + uploaded resumes)
```

### Useful commands

```bash
docker compose logs -f backend   # tail backend logs
docker compose ps                # service status
docker compose exec backend python -m app.cli create-user \
  --email jane@example.com --password 'a-strong-password' --name "Jane Doe"   # add another attorney
```

A `Makefile` wraps the common ones: `make up`, `make down`, `make reset`, `make logs`, `make test`.

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

**Backend** (pytest; uses in-memory SQLite and a captured email outbox, so the stack doesn't need
to be running):

```bash
docker compose build backend
docker compose run --rm --no-deps backend pytest
docker compose run --rm --no-deps backend ruff check .      # lint
```

**Frontend** (type-check + lint in a throwaway Node container):

```bash
docker run --rm -v "$PWD/frontend:/app" -v /app/node_modules -w /app node:22-alpine \
  sh -c "npm install --no-audit --no-fund && npm run typecheck && npm run lint"
```

The frontend Docker image also type-checks during `next build`, so `docker compose up --build`
fails if there are type errors.

Or run both with `make test`.

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

## Repository layout

```
backend/
  app/
    api/            # FastAPI routers (v1) and dependency wiring
    core/           # settings, security (JWT/bcrypt), domain errors, logging
    db/             # SQLAlchemy base + session
    models/         # ORM models (Lead, User)
    schemas/        # Pydantic request/response models
    repositories/   # data access
    services/       # business logic: leads, auth, notifications, email + storage adapters
    cli.py          # admin commands (create-user, seed)
  alembic/          # migrations
  tests/
frontend/
  src/
    app/            # pages (public form, login, leads dashboard) + route handlers proxying the API
    components/     # client components (forms, buttons)
    lib/            # server-side API client, session cookie helpers, types
    middleware.ts   # guards /leads/*
docs/system-design.md
docker-compose.yml
```
