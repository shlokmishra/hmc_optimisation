#!/bin/bash
#SBATCH --job-name=rhgd-reproduce
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:30:00
#SBATCH --output=logs/rhgd-%j.out
#SBATCH --error=logs/rhgd-%j.err

set -euo pipefail
: "${RHGD_CASE:?Set RHGD_CASE to one panel from the reproduction plan}"
cd "${SLURM_SUBMIT_DIR:?Submit from the project root}"
source scripts/activate_env.sh
python -u scripts/reproduce_rhgd.py run --case "$RHGD_CASE" \
    --output "results/reproduction/${RHGD_CASE}-${SLURM_JOB_ID}"
if [[ "${RHGD_VERIFY_AUTHOR:-0}" == "1" ]]; then
    python -u scripts/verify_rhgd_author.py "results/reproduction/${RHGD_CASE}-${SLURM_JOB_ID}"
fi
