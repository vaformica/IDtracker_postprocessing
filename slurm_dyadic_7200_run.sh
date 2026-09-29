#!/usr/bin/env bash
set -euo pipefail

root=/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_fight_7200_frames_psc_v1_5_1_processor_0_8_1_20260928
python=/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python

"$python" "$root/code_docfix_v2/dyadic_7200_release.py" run "$root" "$SLURM_ARRAY_TASK_ID"
