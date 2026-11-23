#!/bin/bash
#SBATCH --job-name=stat605-spectral
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:20:00

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the project root on Grace}"
source scripts/activate_env.sh
python -u scripts/stat605.py spectral --config configs/stat605/spectral_pilot.json \
    --output "${SPECTRAL_OUTPUT:-results/stat605/spectral-pilot-${SLURM_JOB_ID}}"
