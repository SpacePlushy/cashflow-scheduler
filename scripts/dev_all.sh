#!/usr/bin/env bash
set -euo pipefail

# One-shot dev runner: sets up the Python venv, starts the API and UI,
# waits for readiness, and prints the URL to open.
#
# Usage:
#   bash scripts/dev_all.sh            # setup + run, prints link
#   bash scripts/dev_all.sh --open     # also open the browser
#   bash scripts/dev_all.sh --no-reload  # run API without --reload

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OPEN_BROWSER=0
API_RELOAD=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --open) OPEN_BROWSER=1 ;;
    --no-reload) API_RELOAD=0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

echo "[1/5] Bootstrapping Python venv (+ deps)…"
bash scripts/bootstrap_venv.sh --no-tests --no-editable || true
# Ensure editable install
source .venv/bin/activate
pip install -e . >/dev/null

echo "[2/5] Checking Node.js tooling…"
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Please install Node.js (>=18) from https://nodejs.org/ and rerun." >&2
  exit 1
fi

echo "[3/5] Installing UI dependencies (if needed)…"
if [[ ! -d ui/node_modules ]]; then
  (cd ui && npm install)
fi

API_HOST=127.0.0.1
API_PORT=8000
UI_HOST=localhost
UI_PORT=5173

echo "[4/5] Starting API (FastAPI @ http://${API_HOST}:${API_PORT})…"
if [[ ${API_RELOAD} -eq 1 ]]; then
  uvicorn cashflow.api.app:app \
    --reload --reload-dir cashflow \
    --reload-exclude '.venv/*' --reload-exclude 'ui/*' \
    --host ${API_HOST} --port ${API_PORT} > .api.log 2>&1 &
else
  uvicorn cashflow.api.app:app --host ${API_HOST} --port ${API_PORT} > .api.log 2>&1 &
fi
API_PID=$!

echo "[5/5] Starting UI (Vite @ http://${UI_HOST}:${UI_PORT})…"
(cd ui && npm run dev > ../.ui.log 2>&1 &)
UI_PID=$!

cleanup() {
  echo "\nShutting down…"
  kill ${UI_PID} >/dev/null 2>&1 || true
  kill ${API_PID} >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "Waiting for API to become ready…"
API_READY=0
for i in {1..120}; do
  if curl -fsS "http://${API_HOST}:${API_PORT}/health" >/dev/null 2>&1; then API_READY=1; break; fi
  sleep 0.5
done

echo "Waiting for UI dev server…"
UI_READY=0
for i in {1..120}; do
  if curl -fsS "http://${UI_HOST}:${UI_PORT}" >/dev/null 2>&1; then UI_READY=1; break; fi
  sleep 0.5
done

if [[ ${API_READY} -ne 1 ]]; then
  echo "API failed to start. See .api.log for details." >&2
  tail -n 80 .api.log || true
  exit 1
fi

if [[ ${UI_READY} -ne 1 ]]; then
  echo "UI failed to start. See .ui.log for details." >&2
  tail -n 80 .ui.log || true
  exit 1
fi

URL="http://${UI_HOST}:${UI_PORT}"
echo "\nAll set! Open: ${URL}"
if [[ ${OPEN_BROWSER} -eq 1 ]]; then
  if command -v open >/dev/null 2>&1; then open "${URL}"; fi
  if command -v xdg-open >/dev/null 2>&1; then xdg-open "${URL}"; fi
fi

echo "\nLogs:"
echo "  API: tail -f .api.log"
echo "  UI : tail -f .ui.log"
echo "\nPress Ctrl+C to stop both servers."

# Wait on background processes
wait
