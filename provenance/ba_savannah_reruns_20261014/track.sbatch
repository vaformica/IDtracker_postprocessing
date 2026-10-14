#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=08:00:00
set -euo pipefail
umask 0007
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
export MPLCONFIGDIR=/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_savannah_reruns_20261014/mpl_${SLURM_JOB_ID}
exec /home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python /data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_savannah_reruns_20261014/track_one.py "$SLURM_ARRAY_TASK_ID"
