#!/usr/bin/env bash
# End-to-end smoke: compose stack → health → TIFF upload → prediction poll.
# Intended for GitHub Actions and optional local runs from the repo root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
BASE_URL="${SMOKE_API_BASE_URL:-http://127.0.0.1:${API_PORT}}"
ADMIN_INITIAL_PASSWORD="${ADMIN_INITIAL_PASSWORD:-dropsort-admin-dev}"
TIFF_PATH="${SMOKE_TIFF_PATH:-${ROOT}/app/classifier/eval/golden_images/26_file_folder_2931.tif}"
HEALTH_TIMEOUT_SEC="${SMOKE_HEALTH_TIMEOUT_SEC:-180}"
PREDICT_TIMEOUT_SEC="${SMOKE_PREDICT_TIMEOUT_SEC:-300}"
POLL_INTERVAL_SEC="${SMOKE_POLL_INTERVAL_SEC:-3}"

if [[ ! -f "$TIFF_PATH" ]]; then
  echo "::error::Smoke TIFF not found at $TIFF_PATH"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "::error::docker is required"
  exit 1
fi

dc() {
  docker compose "$@"
}

echo "==> Building API image"
dc build api

echo "==> Starting stack (db, redis, vault, minio, sftp, vault-seed, migrate, api, worker)"
dc up -d db redis vault minio sftp vault-seed migrate api worker

echo "==> Waiting for API health (ok=true) — timeout ${HEALTH_TIMEOUT_SEC}s"
HEALTH_DEADLINE=$((SECONDS + HEALTH_TIMEOUT_SEC))
while (( SECONDS < HEALTH_DEADLINE )); do
  if out="$(curl -sfS "${BASE_URL}/health" 2>/dev/null || true)"; then
    if echo "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('ok') else 1)" 2>/dev/null; then
      echo "Health OK"
      break
    fi
  fi
  sleep 2
done

if ! curl -sfS "${BASE_URL}/health" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('ok') else 1)"; then
  echo "::error::API did not become healthy within ${HEALTH_TIMEOUT_SEC}s"
  dc logs --tail=80 api || true
  exit 1
fi

echo "==> Login as admin"
LOGIN_JSON="$(curl -sfS -X POST "${BASE_URL}/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin%40example.com&password=${ADMIN_INITIAL_PASSWORD}")"
TOKEN="$(echo "$LOGIN_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")"

echo "==> Upload TIFF"
UPLOAD_JSON="$(curl -sfS -X POST "${BASE_URL}/batches/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@${TIFF_PATH};type=image/tiff")"
echo "$UPLOAD_JSON" | python3 -m json.tool >/dev/null
echo "Upload accepted."

echo "==> Poll GET /predictions/recent (timeout ${PREDICT_TIMEOUT_SEC}s)"
PRED_DEADLINE=$((SECONDS + PREDICT_TIMEOUT_SEC))
found=""
while (( SECONDS < PRED_DEADLINE )); do
  count="$(curl -sfS "${BASE_URL}/predictions/recent?limit=20" \
    -H "Authorization: Bearer ${TOKEN}" \
    | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")"
  if [[ "${count}" -ge 1 ]]; then
    found=1
    break
  fi
  sleep "${POLL_INTERVAL_SEC}"
done

if [[ -z "${found}" ]]; then
  echo "::error::No predictions appeared before timeout"
  dc logs --tail=120 worker || true
  dc logs --tail=120 api || true
  exit 1
fi

echo "Smoke passed: at least one prediction row is visible via the API."
