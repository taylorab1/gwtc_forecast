#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="gwtc_forecast"

# The software environment is deliberately laptop-local.  The LaCie disk is
# required only for public GW data, processed scientific contracts, large
# temporary files, and results.  Requiring the mount during installation made
# ordinary unit-test and documentation work unnecessarily fragile.
if command -v mamba >/dev/null 2>&1; then
  SOLVER=mamba
elif command -v conda >/dev/null 2>&1; then
  SOLVER=conda
else
  echo "ERROR: neither mamba nor conda is available in PATH." >&2
  exit 2
fi

cd "${REPO_ROOT}"

if "${SOLVER}" env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  "${SOLVER}" env update -n "${ENV_NAME}" -f environment.yml --prune
else
  "${SOLVER}" env create -n "${ENV_NAME}" -f environment.yml
fi

"${SOLVER}" run -n "${ENV_NAME}" python -m pip install --no-deps -e .
"${SOLVER}" run -n "${ENV_NAME}" pytest -q
"${SOLVER}" run -n "${ENV_NAME}" ruff check src tests
"${SOLVER}" run -n "${ENV_NAME}" gwtc-forecast audit-repo

"${REPO_ROOT}/scripts/install_git_guard.sh" || true
"${REPO_ROOT}/scripts/lock_environment.sh"

echo
echo "Environment ready. The external disk was not required for setup."
echo "Activate with:"
echo "  conda activate ${ENV_NAME}"
echo "or:"
echo "  source ${REPO_ROOT}/scripts/activate_project.sh"
echo
echo "Before data or result operations, connect the disk and run:"
echo "  gwtc-forecast bootstrap"
