#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"
RUN="${REPO_ROOT}/scripts/run_in_env.sh"
"${RUN}" gwtc-forecast inventory
"${RUN}" gwtc-forecast pe-index
"${RUN}" gwtc-forecast inspect-selection
"${RUN}" gwtc-forecast discover-hyperposteriors
"${RUN}" gwtc-forecast science-smoke
"${RUN}" gwtc-forecast readiness
