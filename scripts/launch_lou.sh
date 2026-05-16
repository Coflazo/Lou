#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_URL="http://localhost:${BACKEND_PORT}"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"
REUSE_RUNNING="${LOU_REUSE_RUNNING:-0}"
VENV_DIR="$ROOT_DIR/.venv"
LOG_DIR="$ROOT_DIR/.lou-runtime"
BACKEND_PID=""
FRONTEND_PID=""

log() {
  printf "\033[1;34m[lou]\033[0m %s\n" "$*"
}

fail() {
  printf "\033[1;31m[lou]\033[0m %s\n" "$*" >&2
  exit 1
}

cleanup() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

port_has_http() {
  local url="$1"
  curl -fsS "$url" >/dev/null 2>&1
}

load_keys() {
  if [[ -f "$ROOT_DIR/api-keys.txt" ]]; then
    while IFS='=' read -r key value; do
      [[ -z "${key// }" ]] && continue
      [[ "$key" == \#* ]] && continue
      export "$key=$value"
    done < "$ROOT_DIR/api-keys.txt"
  fi
}

wait_for_url() {
  local url="$1"
  local label="$2"
  for _ in $(seq 1 60); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  fail "$label did not become ready at $url"
}

trap cleanup EXIT

log "Checking required tools"
require_command python3
require_command node
require_command npm
require_command curl

log "Loading local API keys from api-keys.txt if present"
load_keys

log "Preparing Python environment"
if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install -r backend/requirements.txt >/dev/null

log "Preparing frontend dependencies"
if [[ ! -d frontend/node_modules ]]; then
  npm --prefix frontend install
else
  npm --prefix frontend install >/dev/null
fi

if [[ ! -f demo-data/lou-pioneer-playbook-datasets-50.jsonl ]]; then
  log "Generating Pioneer playbook dataset"
  python scripts/generate_lou_dataset.py --count 50 >/dev/null
else
  log "Using existing Pioneer playbook dataset"
fi

log "Running backend tests"
python -m pytest backend/tests/test_lou_flows.py

log "Running frontend role tests"
npm --prefix frontend test

log "Building frontend production bundle"
npm --prefix frontend run build

mkdir -p "$LOG_DIR"

if port_has_http "$BACKEND_URL/api/health"; then
  if [[ "$REUSE_RUNNING" == "1" ]]; then
    log "Backend already responding at $BACKEND_URL; reusing because LOU_REUSE_RUNNING=1"
  else
    fail "Backend is already running at $BACKEND_URL. Stop it first, set BACKEND_PORT, or run with LOU_REUSE_RUNNING=1."
  fi
else
  if lsof -iTCP:"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    fail "Port $BACKEND_PORT is in use by a non-Lou process. Stop it or set BACKEND_PORT."
  fi
  log "Starting backend on $BACKEND_URL"
  PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" >"$LOG_DIR/backend.log" 2>&1 &
  BACKEND_PID="$!"
  wait_for_url "$BACKEND_URL/api/health" "Backend"
fi

log "Running live backend smoke checks"
python scripts/smoke_lou.py "$BACKEND_URL"

if port_has_http "$FRONTEND_URL"; then
  if [[ "$REUSE_RUNNING" == "1" ]]; then
    log "Frontend already responding at $FRONTEND_URL; reusing because LOU_REUSE_RUNNING=1"
  else
    fail "Frontend is already running at $FRONTEND_URL. Stop it first, set FRONTEND_PORT, or run with LOU_REUSE_RUNNING=1."
  fi
else
  if lsof -iTCP:"$FRONTEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    fail "Port $FRONTEND_PORT is in use by a non-Lou process. Stop it or set FRONTEND_PORT."
  fi
  log "Starting built frontend preview on $FRONTEND_URL"
  (cd frontend && npm exec -- vite preview --host 0.0.0.0 --port "$FRONTEND_PORT") >"$LOG_DIR/frontend.log" 2>&1 &
  FRONTEND_PID="$!"
  wait_for_url "$FRONTEND_URL" "Frontend"
fi

log "Launch checks passed"
log "Frontend: $FRONTEND_URL"
log "Backend:  $BACKEND_URL"
log "Runtime logs: $LOG_DIR"
log "Keep this terminal open. Press Ctrl+C to stop services started by this launcher."

if [[ -n "${BACKEND_PID}${FRONTEND_PID}" ]]; then
  wait
else
  while true; do
    sleep 3600
  done
fi
