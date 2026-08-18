#!/bin/sh
set -eu

corepack enable
cd ui
pnpm install --frozen-lockfile
pnpm build
cd ..

PYTHONPATH=src uv run --no-dev python -m infra.postgres.execute_migrations
