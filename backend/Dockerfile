FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so they are cached independently of source changes.
COPY pyproject.toml ./
RUN python -c "import tomllib; p=tomllib.load(open('pyproject.toml','rb'))['project']; print('\n'.join(p['dependencies'] + p['optional-dependencies']['dev']))" > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt

COPY . .

RUN chmod +x scripts/start.sh \
    && useradd --create-home appuser \
    && mkdir -p /data/uploads \
    && chown -R appuser /app /data
USER appuser

EXPOSE 8000
CMD ["./scripts/start.sh"]
