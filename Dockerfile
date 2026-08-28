# checkov:skip=CKV_DOCKER_2,CKV_DOCKER_3 (local dev uniquement)
FROM python:3.13.5-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock* ./

RUN uv venv && uv sync --no-dev

COPY src/ ./src/
COPY migrations/ ./migrations/

CMD ["sh", "-c", "PYTHONPATH=src .venv/bin/python -m infra.postgres.execute_migrations && exec .venv/bin/uvicorn serveur:app --host 0.0.0.0 --port 3001 --reload --app-dir src"]
