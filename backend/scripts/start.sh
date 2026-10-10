#!/usr/bin/env sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding attorney user (if configured)..."
python -m app.cli seed

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" "$@"
