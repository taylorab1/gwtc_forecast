#!/usr/bin/env bash
# Source this file: source scripts/activate_project.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="gwtc_forecast"
if ! command -v conda >/dev/null 2>&1; then
  echo "ERROR: conda is not available in PATH." >&2
  return 2 2>/dev/null || exit 2
fi

eval "$(conda shell.bash hook)"
conda activate "${ENV_NAME}"
cd "${REPO_ROOT}"

if PATH_EXPORTS="$(gwtc-forecast paths 2>/dev/null)"; then
  eval "${PATH_EXPORTS}"
  echo "External scientific data root: ${GWTC_DATA_ROOT}"
else
  echo "Configured external storage is not safely mounted; development mode only."
  echo "Data/result commands will fail closed until the storage guard passes."
fi

echo "Activated ${ENV_NAME}"
echo "Repository: ${REPO_ROOT}"
