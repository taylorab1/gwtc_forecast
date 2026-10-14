#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if ! command -v conda >/dev/null 2>&1; then
  echo 'Conda not found. Use your existing Python >=3.11 environment and pip install -e ".[dev]"; no cluster or external data required.' >&2
  exit 2
fi
if conda env list | awk '{print $1}' | grep -qx gwtc_forecast; then
  echo 'Existing gwtc_forecast environment found; preserving it (not downgrading/removing science packages).'
else
  conda env create -f environment-core.yml
fi
conda run --no-capture-output -n gwtc_forecast python -m pip install --no-deps -e .
conda run --no-capture-output -n gwtc_forecast python -m pytest -q
printf '\nReady. Activate: conda activate gwtc_forecast\n'
printf 'For real-data fitting, install/verify the optional science environment at the relevant milestone.\n'
