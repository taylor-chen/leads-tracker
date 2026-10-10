# Stages: `base` has the runtime dependencies, `test` adds the dev tools (pytest, ruff) for
# `make test-backend` / `make lint-backend`, and `runtime` (the default, used by compose) doesn't.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies first so they are cached independently of source changes.
COPY pyproject.toml ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt


FROM base AS test

RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['optional-dependencies']['dev']))" > /tmp/requirements-dev.txt \
    && pip install -r /tmp/requirements-dev.txt
COPY . .
CMD ["pytest"]


FROM base AS runtime

COPY . .

RUN chmod +x scripts/start.sh \
    && useradd --create-home appuser \
    && mkdir -p /data/uploads \
    && chown -R appuser /app /data
USER appuser

EXPOSE 8000
CMD ["./scripts/start.sh"]
