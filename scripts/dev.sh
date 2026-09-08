#!/usr/bin/env bash
# Run the backend (uvicorn --reload) and the frontend (vite) together.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/backend/.venv/Scripts/python.exe"
[ -x "$PY" ] || PY="$ROOT/backend/.venv/bin/python"

( cd "$ROOT/backend" && "$PY" -m uvicorn app.main:app --reload --port "${PORT:-8000}" ) &
BACK=$!
trap 'kill "$BACK" 2>/dev/null || true' EXIT INT TERM

( cd "$ROOT/frontend" && npm run dev )
