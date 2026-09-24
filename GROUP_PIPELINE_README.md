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
The Firebird GUI exposes the automatic pile parameters (gap search growth,
radius cap, maximum gap frames, split confirmation, and distant-return
confirmation). Their defaults are 20 px/frame, 300 px, 30 frames, three
frames, and ten frames, respectively. Change them
by making a new automatic run; frame review decisions do not alter the model.
PSC model 1.4.0 also gates every member of a split or merged pile by its own
last defensible position. A short distant IDtracker label cannot pull a
hidden beetle to another beetle. An unseen member of an ambiguous multiway
split is marked `UNRESOLVED_SPLIT` with no location until the evidence
supports a return. The same rule applies to dyadic and larger groups.

The analysis bundle contains its PDF, canonical and raw coordinate tables,
`frame_data.csv`, pair and fungus summaries, and a hashed manifest. The review
folder contains a synchronized HTML viewer and its video. These are
**UNREVIEWED** inference outputs until checked against the source recording.

## Review and correct the synchronized video

Open `review/interaction_review.html` with its `review_video.mp4` beside it.
For reliable seeking in a browser preview, you can also run
`python serve_review.py /path/to/review --port 8769` and open the localhost URL
it prints; this serves only that folder and supports MP4 byte ranges.
Expand **Review and correct frames**. For a long episode, turn on **Select range
on timeline** and drag along a pair row. The inclusive frame range and pair
fill in; the beetle inferred more often in that interval is selected first.
Check that choice, enter reviewer and reason, then use a one-click PSC action
or the detailed controls. The viewer can override
presumed social contact, visible proximity, the beetle's location (raw,
missing, or co-located with a detected partner), and fungus identity. The
timeline, video overlay, and beetle-status panel update immediately. Gray pair
segments mean pile membership remains plausible but no position was detected;
those frames do not contribute automatic distance or fungus occupancy.
The automatic model treats multiple IDtracker identity coordinates near a
single segmented blob as one visible anchor plus inferred pile members. It
does not count the coordinates as independent sightings.

Use **Export review log** to save a JSON record bound to the exact automatic
bundle hashes. It contains each dated decision and can be imported back into
the same viewer. The browser does not overwrite the source CSVs or TOMLs. To
create a new reviewed CSV bundle and a portable reviewed HTML/video folder:

```sh
python apply_review_decisions.py /path/to/analysis \
  /path/to/beetle_review_FIRST_LAST.json /new/reviewed_output \
  --source-review /path/to/review
```

The reviewed output has frame-level human-intervention flags, raw and reviewed
coordinates, pair labels, fungus and movement data, summaries, the decision
log, and a hash manifest. A fungus correction needs a supported or manually
reviewed coordinate. These are attributed training candidates; do not merge
them silently into automatic results. Changing the algorithm's global search
and split thresholds requires a fresh processing run, not a frame annotation.

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
