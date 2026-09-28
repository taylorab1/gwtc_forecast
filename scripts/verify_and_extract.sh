#!/usr/bin/env bash
set -euo pipefail
RUN="$(cd "$(dirname "$0")" && pwd)/run_in_env.sh"
"${RUN}" gwtc-forecast verify "$@"
"${RUN}" gwtc-forecast extract "$@"
"${RUN}" gwtc-forecast inventory
