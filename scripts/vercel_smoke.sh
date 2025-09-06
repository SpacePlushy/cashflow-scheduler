#!/usr/bin/env bash
set -euo pipefail

# Vercel + Fly end-to-end smoke tester
#
# This script uses the Vercel CLI to pull production env vars from your
# UI and API projects, validates the expected wiring, then runs the
# repo's Node smoke script against your live deployments.
#
# Requirements:
# - vercel CLI installed and logged in (vercel whoami)
# - node available to run scripts/smoke.mjs
#
# Usage examples:
#   scripts/vercel_smoke.sh \
#     --ui-url https://your-ui.vercel.app \
#     --api-url https://your-api.vercel.app/api \
#     --verify-url https://cashflow-check-xxxxx.fly.dev
#
# Optional team scope / custom paths:
#   scripts/vercel_smoke.sh --team your-team --ui-cwd ./web --api-cwd . ...
#
# Notes:
# - If you omit --api-url or --verify-url, the script will fall back to values
#   found in your UI project's production env vars (NEXT_PUBLIC_API_BASE,
#   NEXT_PUBLIC_VERIFY_BASE).
# - If you omit --ui-url, we cannot reliably discover it via CLI; please pass it.

# Working directories linked to the respective Vercel projects
UI_CWD="./web"
API_CWD="."
UI_URL=""
API_URL=""
VERIFY_URL=""
TEAM_FLAG=() # e.g., ("--scope" "team_xxx")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ui-cwd) UI_CWD="$2"; shift 2;;
    --api-cwd) API_CWD="$2"; shift 2;;
    --ui-url) UI_URL="$2"; shift 2;;
    --api-url) API_URL="$2"; shift 2;;
    --verify-url) VERIFY_URL="$2"; shift 2;;
    --team|--scope) TEAM_FLAG=("--scope" "$2"); shift 2;;
    -h|--help)
      sed -n '1,80p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

if ! command -v vercel >/dev/null 2>&1; then
  echo "vercel CLI is not installed or not in PATH." >&2
  echo "Install: npm i -g vercel" >&2
  exit 2
fi
if ! command -v node >/dev/null 2>&1; then
  echo "node is required to run scripts/smoke.mjs" >&2
  exit 2
fi

echo "Checking Vercel authentication..." >&2
vercel whoami ${TEAM_FLAG+"${TEAM_FLAG[@]}"} >/dev/null 2>&1 || { echo "Run 'vercel login' first" >&2; exit 2; }

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "Pulling production env for UI project (cwd=$UI_CWD)" >&2
vercel env pull "$tmpdir/.env.ui" --yes --environment production --cwd "$UI_CWD" ${TEAM_FLAG+"${TEAM_FLAG[@]}"} >/dev/null

echo "Pulling production env for API project (cwd=$API_CWD)" >&2
vercel env pull "$tmpdir/.env.api" --yes --environment production --cwd "$API_CWD" ${TEAM_FLAG+"${TEAM_FLAG[@]}"} >/dev/null

source_env() { # source KEY=VALUE file while preserving existing env
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    key=${line%%=*}
    val=${line#*=}
    # strip optional quotes
    val=${val%$'\r'}
    # remove surrounding single/double quotes if present
    case "$val" in
      \"*) val=${val#\"};;
    esac
    case "$val" in
      *\") val=${val%\"};;
    esac
    case "$val" in
      "'*") val=${val#\'};;
    esac
    case "$val" in
      *"'") val=${val%\'};;
    esac
    export "$key"="$val"
  done < "$1"
}

source_env "$tmpdir/.env.ui"
source_env "$tmpdir/.env.api"

# Prefer explicit flags, else fall back to UI env
API_URL=${API_URL:-${NEXT_PUBLIC_API_BASE:-}}
VERIFY_URL=${VERIFY_URL:-${NEXT_PUBLIC_VERIFY_BASE:-}}

# Resolve bypass secret preference order: UI override then API
# Source order was UI first, then API; at this point env holds merged values
BYPASS=${API_BYPASS_SECRET:-${VERCEL_AUTOMATION_BYPASS_SECRET:-}}

echo
echo "Resolved configuration:"
printf '  UI URL:     %s\n' "${UI_URL:-'(required, not provided)'}"
printf '  API URL:    %s\n' "${API_URL:-'(from NEXT_PUBLIC_API_BASE or --api-url)'}"
printf '  Verify URL: %s\n' "${VERIFY_URL:-'(from NEXT_PUBLIC_VERIFY_BASE or --verify-url)'}"
printf '  Bypass:     %s\n' "${BYPASS:+(set)}"
echo

# Warnings for common misconfigurations
warn=0
if printf %s "$API_URL" | grep -qE "[[:space:]]|\\n"; then
  echo "Warning: API URL contains whitespace/newline; trim it in Vercel env." >&2
  warn=1
fi
if printf %s "${NEXT_PUBLIC_API_BASE:-}" | grep -qE "[[:space:]]|\\n"; then
  echo "Warning: NEXT_PUBLIC_API_BASE in UI env contains whitespace/newline; trim it." >&2
  warn=1
fi
if printf %s "${NEXT_PUBLIC_VERIFY_BASE:-}" | grep -qE "[[:space:]]|\\n"; then
  echo "Warning: NEXT_PUBLIC_VERIFY_BASE in UI env contains whitespace/newline; trim it." >&2
  warn=1
fi
if [[ "$warn" -eq 1 ]]; then echo; fi

err=0
if [[ -z "$UI_URL" ]]; then echo "Error: --ui-url is required to test the site." >&2; err=1; fi
if [[ -z "$API_URL" ]]; then echo "Error: API URL could not be determined. Set NEXT_PUBLIC_API_BASE in UI project or pass --api-url." >&2; err=1; fi
if [[ $err -ne 0 ]]; then exit 2; fi

echo "Running smoke tests against live deployments..." >&2
UI_URL="$UI_URL" API_URL="$API_URL" VERIFY_URL="$VERIFY_URL" BYPASS="$BYPASS" \
  node scripts/smoke.mjs

echo "\nSmoke OK. UI, API, and Verify (if configured) are healthy." >&2
