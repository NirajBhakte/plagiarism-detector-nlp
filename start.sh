#!/usr/bin/env bash
# Render start script — bind $PORT immediately; model loads in a background thread.
set -euo pipefail

if [ -z "${PORT:-}" ]; then
  echo "ERROR: PORT is not set"
  exit 1
fi

echo "==> Starting uvicorn on 0.0.0.0:${PORT}"
exec uvicorn src.api:app --host 0.0.0.0 --port "${PORT}"
