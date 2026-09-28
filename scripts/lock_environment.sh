#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="gwtc_forecast"
OUT="${REPO_ROOT}/environment-locks"
mkdir -p "${OUT}"

conda env export -n "${ENV_NAME}" --from-history > "${OUT}/environment.from-history.yml"
conda list -n "${ENV_NAME}" --explicit > "${OUT}/conda-explicit.txt"
conda run -n "${ENV_NAME}" python -m pip freeze > "${OUT}/pip-freeze.txt"
conda run -n "${ENV_NAME}" python -c 'import platform,sys; print(sys.version); print(platform.platform()); print(platform.machine())' > "${OUT}/runtime.txt"

echo "Environment locks written to ${OUT}"
