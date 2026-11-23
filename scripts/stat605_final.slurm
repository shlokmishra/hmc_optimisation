#!/bin/bash
#SBATCH --job-name=stat605-final
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from project root}"
source scripts/activate_env.sh
export PYTHONPATH="$PWD/src"
python -u -m stat605.final_study "$@"
