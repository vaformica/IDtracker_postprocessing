#!/bin/bash
#SBATCH --job-name=charlotte_compare
#SBATCH --partition=compute
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/comparison-%j.log
set -euo pipefail
export MPLCONFIGDIR="$SLURM_SUBMIT_DIR/mpl_comparison"
cd "$SLURM_SUBMIT_DIR"
exec /home/vformic1-swat/miniconda3/envs/idtracker_reprocess_v1/bin/python collect.py
