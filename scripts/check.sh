#!/usr/bin/env bash
# Lint + typecheck + tests for both apps.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/backend/.venv/Scripts/python.exe"
[ -x "$PY" ] || PY="$ROOT/backend/.venv/bin/python"

echo "== backend: ruff =="
"$PY" -m ruff check "$ROOT/backend"
echo "== backend: ruff format --check =="
"$PY" -m ruff format --check "$ROOT/backend"
echo "== backend: pytest =="
( cd "$ROOT/backend" && "$PY" -m pytest )

echo "== frontend: tsc =="
( cd "$ROOT/frontend" && npx tsc -b --noEmit )
echo "== frontend: vitest =="
( cd "$ROOT/frontend" && npm test )

echo "All checks passed."
