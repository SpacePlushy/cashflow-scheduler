#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a local Python 3.11 virtual environment, install deps, and run tests.
# Usage examples:
#   bash scripts/bootstrap_venv.sh
#   bash scripts/bootstrap_venv.sh --auto-install        # install python@3.11 via Homebrew if missing
#   bash scripts/bootstrap_venv.sh --recreate            # recreate .venv from scratch
#   bash scripts/bootstrap_venv.sh --no-tests            # skip running pytest
#   bash scripts/bootstrap_venv.sh --no-editable         # skip pip install -e .
#   bash scripts/bootstrap_venv.sh --python /path/to/python3.11

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

AUTO_INSTALL=0
RECREATE=0
RUN_TESTS=1
INSTALL_EDITABLE=1
PY_BIN=""
RUN_CMD=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto-install) AUTO_INSTALL=1 ;;
    --recreate) RECREATE=1 ;;
    --no-tests) RUN_TESTS=0 ;;
    --no-editable) INSTALL_EDITABLE=0 ;;
    --python) shift; PY_BIN="${1:-}" ;;
    --run) shift; RUN_CMD="${1:-}" ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

# Choose Python 3.11 interpreter
if [[ -n "$PY_BIN" ]]; then
  PYTHON="$PY_BIN"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON="$(command -v python3.11)"
elif [[ -x /opt/homebrew/bin/python3.11 ]]; then
  PYTHON="/opt/homebrew/bin/python3.11"
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; import sys; sys.exit(0 if sys.version_info>=(3,11) else 1)'; then
  PYTHON="python3"
else
  echo "Python 3.11+ not found." >&2
  if command -v brew >/dev/null 2>&1; then
    if [[ $AUTO_INSTALL -eq 1 ]]; then
      echo "Installing python@3.11 via Homebrew..."
      brew install python@3.11
      PYTHON="/opt/homebrew/bin/python3.11"
    else
      echo "Tip: rerun with --auto-install to install via Homebrew, or provide --python /path/to/python3.11" >&2
      exit 1
    fi
  else
    echo "Please install Python 3.11 and rerun, or pass --python path." >&2
    exit 1
  fi
fi

echo "Using: $($PYTHON -V)"

if [[ $RECREATE -eq 1 && -d .venv ]]; then
  echo "Removing existing .venv ..."
  rm -rf .venv
fi

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv at .venv ..."
  "$PYTHON" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip ..."
python -m pip install -U pip

echo "Installing requirements ..."
pip install -r requirements.txt

if [[ $INSTALL_EDITABLE -eq 1 ]]; then
  echo "Installing project in editable mode ..."
  pip install -e .
fi

if [[ $RUN_TESTS -eq 1 ]]; then
  echo "Running tests ..."
  pytest -q
fi

if [[ -n "$RUN_CMD" ]]; then
  echo "Running command in venv: $RUN_CMD"
  bash -lc "$RUN_CMD"
fi

echo "Done. The venv was active only for this script's run."
echo "To work interactively later: source .venv/bin/activate"
