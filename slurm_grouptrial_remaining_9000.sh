#!/usr/bin/env bash
set -euo pipefail

root=/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/grouptrial_2024_remaining_5_9000frames_psc_v1_5_1_processor_0_8_1_20260928
python=/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1

"$python" "$root/code_processfix_v1/grouptrial_remaining_9000.py" "$1" "$root" "$SLURM_ARRAY_TASK_ID"
