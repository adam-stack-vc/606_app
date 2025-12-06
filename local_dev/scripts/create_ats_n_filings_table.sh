#!/bin/bash

set -e

# Create ats_n_filings table in local Postgres "stack_equities"
# Environment overrides allowed: DB_HOST, DB_PORT, DB_USER, DB_NAME

# Load .env if present (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Prefer DB_PASSWORD from .env if available, else keep existing PGPASSWORD
if [ -n "$DB_PASSWORD" ]; then
  export PGPASSWORD="$DB_PASSWORD"
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-stack_equities}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DDL_PATH="${SCRIPT_DIR}/create_ats_n_filings_table.sql"

if [ ! -f "$DDL_PATH" ]; then
  echo "❌ DDL not found at $DDL_PATH"
  exit 1
fi

echo "Creating table public.ats_n_filings in database: ${DB_NAME}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$DDL_PATH"
echo "✅ Done."


