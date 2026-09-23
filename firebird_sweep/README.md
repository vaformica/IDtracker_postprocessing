# Charlotte six-beetle grid sweep

`make_grid.py` prepares 60 TOMLs from the three saved trial01 session records.
Each source contributes two paired controls (original intensity/area, background
on and off) and 18 shared-grid runs. The shared grid uses minimum blob areas
250, 400, 550 pixels²; background-on lower intensity cutoffs30,50,70 (upper255);
and background-off upper cutoffs123,143,163 (lower0). Maximum area remains
unbounded. ROI geometry and six-animal counts are preserved. Tracking intervals
are standardized to [422,16998], analysis to inclusive422–7622 at30fps.

`run.slurm` is a 60-task GPU array capped at3 concurrent tasks,8CPUs/48GB and2h
per task. `run_task.py` preserves every log, requires independent session
completion evidence even if IDtracker exits1, records original-coordinate
missingness/IDtracker quality statistics, and invokes the complete v0.7.0
persistent-pile pipeline. Every successful run contains the 13-page PDF,
canonical and raw-coordinate CSVs, provenance manifests, a cropped MP4, and the
synchronized interactive review HTML. Review/video outputs use the exact same
`canonical_states.npz` that drives the estimated metrics.
`collect.slurm` runs afterany the array; `collect.py` retains failures in CSVs,
creates heatmaps and paired controls, and provides a descriptive shortlist.

This is an unreplicated parameter screen, not a causal estimate across different
beetle groups. OLD and OLD_TEst are weighted together as one group in the
shortlist (25% each, MIX50%). Missingness is not sufficient for selecting defaults:
IDtracker may fill gaps, misidentify beetles, or detect false blobs. Review
segmentation and identity assignments against video before approval. Refinement
around promising settings should follow observed results, not be predeclared as
an optimum. Originals and previous runs are never overwritten.

For ordinary individual-session work, launch `six_beetle_firebird_gui.py` on
the Mac. It discovers Firebird sessions over SSH, exposes proximity, jump,
movement, and ROI-buffer settings, previews the exact command, deploys a hashed
code snapshot, submits a compute Slurm job, and downloads a checksum-verified
portable bundle. The original dyadic GUI remains a separate supported profile;
the six-beetle report layer does not yet support animal counts above six.
