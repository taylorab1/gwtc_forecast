#!/usr/bin/env bash
set -euo pipefail
ENV_NAME="gwtc_forecast"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v conda >/dev/null 2>&1; then
  echo "ERROR: conda is not available. Run scripts/setup_conda.sh first." >&2
  exit 2
fi

cd "${REPO_ROOT}"

# Unit tests, linting, documentation, and local development are valid without
# the external disk.  When the disk is demonstrably mounted, route scientific
# caches and temporary files there.  Commands that read or write scientific
# data still enforce the independent Python-side storage guard.
if PATH_EXPORTS="$(
  conda run --no-capture-output -n "${ENV_NAME}" gwtc-forecast paths 2>/dev/null
)"; then
  eval "${PATH_EXPORTS}"
  mkdir -p \
    "${TMPDIR}" \
    "${XDG_CACHE_HOME}" \
    "${MPLCONFIGDIR}" \
    "${JUPYTER_RUNTIME_DIR}" \
    "${NUMBA_CACHE_DIR}" \
    "${JOBLIB_TEMP_FOLDER}"
else
  echo "NOTE: external disk is not mounted; running in laptop-local development mode." >&2
fi

exec conda run --no-capture-output -n "${ENV_NAME}" "$@"
