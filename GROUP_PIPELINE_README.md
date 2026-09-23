# Reusable beetle group pipeline

The same processor now handles **two or more tracked animals** and an ROI list
containing an arena followed by **one or more fungi**. It reads animal count
from the trajectory array and fungus count from `session.json`. The original
2024 setup (six animals, three fungi) remains supported. IDs in exports are
zero-based tracking identities; fungus numbers follow ROI input order.

## Run analysis, PDF, and synchronized video review

Run this in an environment with the repository's Python dependencies, the
session's IDtracker.ai environment, ffmpeg, and ffprobe available:

```sh
python run_group_pipeline.py \
  --session /path/to/idtracker_session \
  --source-video /path/to/source_video.mp4 \
  --analysis-output /new/output/analysis \
  --review-output /new/output/review \
  --start 422 --end 7622 --fps 30 --label Example
```

`--start` and `--end` are **inclusive global frames**. Set `--idtracker-python`,
`--ffmpeg`, and `--ffprobe` when those tools are outside the default `PATH`.
`--help` lists proximity, movement, jump, ROI-buffer, and crop controls. The
pipeline uses the session's detection evidence; it refuses to invent pile
positions when the evidence is missing. Source trajectories and TOMLs are not
overwritten. Both output folders must be new.

The analysis bundle contains its PDF, canonical and raw coordinate tables,
`frame_data.csv`, pair and fungus summaries, and a hashed manifest. The review
folder contains a synchronized HTML viewer and its video. These are
**UNREVIEWED** inference outputs until checked against the source recording.

For a PDF and CSVs without making the review video, use
`python group_processor.py --help`. It requires a trajectory, session,
analysis start/window, a destination, and detection evidence. The historical
`six_beetle_processor.py` API remains callable; `analyze_group` is the
general-name alias for library users.

## Change the analysis window later

For any complete subwindow already present in the analysis bundle:

```sh
python frame_data.py /path/to/analysis \
  --start 422 --end 4022 --output /new/output/short_window
```

This creates `beetle_summary.csv`, `pair_summary.csv`, and provenance metadata.
Fungus percentages have both all-frame and known-location denominators.
Movement uses accepted adjacent steps whose midpoint falls in a fungus; the
step entering the selected first frame is excluded. The source frame CSV hash
is checked before summarizing. A longer interval than the saved frame data
requires a new tracking/analysis run.

Older canonical bundles can receive a separate frame export with
`python backfill_frame_data.py OLD_BUNDLE NEW_FOLDER`; the old bundle remains
unchanged.

For an SSH-based local interface, run `python group_firebird_gui.py`. Its
profile menu can show all supported sessions, only dyads, or the established
six-beetle/four-ROI sessions. Selecting a session fills its recorded start and
end frames into the analysis fields; review them before submission. The GUI
deploys a hashed code snapshot to Firebird, submits the same shared pipeline,
reports the Slurm job, and can download a verified bundle. The historical
`six_beetle_firebird_gui.py` starts with the six-beetle filter selected but can
also switch profiles. The separate older dyadic `firebird_gui.py` and v0.8.1
processor remain available for comparison; their outputs do not silently mix
with these new persistent-pile estimates.

Tests exercise the core, PDF, HTML, and frame export for 2/1, 6/3, and 7/4
animal/fungus configurations. These are software checks, not validation of
biological identity assignments.

A real 2026 two-beetle/one-fungus Firebird run, its portable reviews, and the
important long-contact caveat are recorded in
[`reports/DYADIC_GENERIC_VALIDATION_2026-09-22.md`](reports/DYADIC_GENERIC_VALIDATION_2026-09-22.md).
