#!/bin/bash
#SBATCH --job-name=gwtc_val_200
#SBATCH --partition=cputest
#SBATCH --qos=simple-qos
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=gwtc_val_200_%j.out
#SBATCH --error=gwtc_val_200_%j.err

set -euo pipefail

cd "$HOME/gwtc_forecast"

export PATH="$HOME/.conda/envs/gwtc_forecast/bin:$PATH"
export GWTC_DATA_ROOT="/Projects/Data/macias/924994587/GW_Project_Data"
export GWTC_RESULTS_ROOT="$GWTC_DATA_ROOT/results"

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

PYTHON="$HOME/.conda/envs/gwtc_forecast/bin/python"

test -x "$PYTHON"
test -d "$GWTC_DATA_ROOT"
test -w "$GWTC_RESULTS_ROOT"

echo "Job ID: $SLURM_JOB_ID"
echo "Host: $(hostname)"
echo "Python: $PYTHON"
echo "Start: $(date)"

/usr/bin/time -v \
"$PYTHON" -m gwtc_forecast.cli feature-calibration \
    --replicates 200 \
    --seed 20261024 \
    --output "$GWTC_RESULTS_ROOT/feature_calibration_validation_200_job_${SLURM_JOB_ID}"

echo "Finish: $(date)"
