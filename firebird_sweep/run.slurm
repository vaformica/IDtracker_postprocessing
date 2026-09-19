#!/bin/bash
#SBATCH --job-name=charlotte_grid
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --array=0-59%3
#SBATCH --output=logs/%A_%a.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="$SLURM_SUBMIT_DIR/mpl_cache_${SLURM_ARRAY_TASK_ID}"
export PYTHONUNBUFFERED=1
cd "$SLURM_SUBMIT_DIR"
exec /home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python run_task.py
