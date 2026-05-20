#!/usr/bin/env bash
# Render START command only (not build). Build command must be: bash build.sh
set -euo pipefail

# #region agent log
_debug_log() {
  local log_path="${DEBUG_LOG_PATH:-$(cd "$(dirname "$0")/.." && pwd)/debug-276265.log}"
  printf '%s\n' "{\"sessionId\":\"276265\",\"hypothesisId\":\"$1\",\"location\":\"start.sh\",\"message\":\"$2\",\"data\":$3,\"timestamp\":$(date +%s)000}" >> "$log_path" 2>/dev/null || true
}
# #endregion

if [ -z "${PORT:-}" ]; then
  echo "ERROR: PORT is not set"
  # #region agent log
  _debug_log "H2" "PORT missing" "{\"port\":\"\"}"
  # #endregion
  exit 1
fi

# #region agent log
_debug_log "H2" "pre-start env" "{\"port\":\"${PORT}\",\"python\":\"$(command -v python || echo missing)\",\"uvicorn_bin\":\"$(command -v uvicorn || echo missing)\",\"python_m_uvicorn\":\"$(python -m uvicorn --version 2>&1 | head -1 || echo missing)\"}"
# #endregion

echo "==> Starting uvicorn on 0.0.0.0:${PORT}"
exec python -m uvicorn src.api:app --host 0.0.0.0 --port "${PORT}"
