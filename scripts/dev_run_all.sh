#!/usr/bin/env bash
# Bootstrap the FastAPI backend and Next.js frontend, then open the web UI.
# Usage: ./scripts/dev_run_all.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_BIND_HOST="${DEV_BACKEND_HOST:-0.0.0.0}"
PUBLIC_HOST_DEFAULT=$(python3 - <<'PY'
import socket

def get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()

print(get_ip())
PY
)
PUBLIC_HOST="${DEV_PUBLIC_HOST:-$PUBLIC_HOST_DEFAULT}"
API_URL="${DEV_PUBLIC_API_URL:-http://${PUBLIC_HOST}:${BACKEND_PORT}}"
UI_HOST="${DEV_UI_HOST:-localhost}"
UI_URL="http://${UI_HOST}:${FRONTEND_PORT}"
BACKEND_LOG="$ROOT_DIR/.tmp/backend.log"
FRONTEND_LOG="$ROOT_DIR/.tmp/frontend.log"

mkdir -p "$ROOT_DIR/.tmp"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

printf '\n[1/5] Ensuring Python dependencies...\n'
if ! python3 -m pip show fastapi >/dev/null 2>&1; then
  python3 -m pip install --user -r "$ROOT_DIR/api/requirements.txt"
fi
if ! python3 -m pip show uvicorn >/dev/null 2>&1; then
  python3 -m pip install --user uvicorn
fi
if ! python3 - <<'PY'
import importlib
import sys
try:
    importlib.import_module("ortools")
except ModuleNotFoundError:
    sys.exit(1)
PY
then
  python3 -m pip install --user "ortools>=9.8"
fi

printf '[2/5] Starting FastAPI backend on %s...\n' "$API_URL"
pushd "$ROOT_DIR" >/dev/null
python3 -m uvicorn api.index:app --host "$BACKEND_BIND_HOST" --port "$BACKEND_PORT" \
  --reload >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
popd >/dev/null

sleep 2
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  printf 'Backend failed to start. Check %s for logs.\n' "$BACKEND_LOG"
  exit 1
fi

printf '[3/5] Ensuring web dependencies...\n'
pushd "$ROOT_DIR/web" >/dev/null
if [[ ! -d node_modules ]]; then
  npm install
fi

printf '[4/5] Launching Next.js dev server on %s...\n' "$UI_URL"
NEXT_PUBLIC_SOLVER_API_URL="$API_URL" npm run dev >"$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
popd >/dev/null

sleep 5
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  printf 'Frontend failed to start. Check %s for logs.\n' "$FRONTEND_LOG"
  exit 1
fi

printf '[5/5] Opening browser at %s\n' "$UI_URL"
if command -v open >/dev/null 2>&1; then
  open "$UI_URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$UI_URL"
else
  printf 'Please open %s manually.\n' "$UI_URL"
fi

printf '\nBackend logs:   %s\nFrontend logs:  %s\n' "$BACKEND_LOG" "$FRONTEND_LOG"
printf 'Press Ctrl+C to stop both servers.\n\n'

wait "$BACKEND_PID" "$FRONTEND_PID"
