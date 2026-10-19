FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY src/ ./src/

CMD ["sh", "-c", "uv run --no-dev uvicorn serveur_mcp:app --app-dir src --host \"${RULA_MCP_HOTE:-0.0.0.0}\" --port \"${RULA_MCP_PORT:-8080}\""]
