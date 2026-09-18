# Six-beetle post-processing: first research-review version

`codex/six-beetles-three-fungus-rois` branches from commit `8fcff29` (July 25,
2026), the current local `processor.py` v0.8.1. The original processor, GUI,
SLURM workers, and QC tools are unchanged. This is a separate command-line entry
point in the same repository so scientific primitives and history stay together.

## Why this baseline

The Codex task **Rework session post-processing**
(`019f9468-d3ff-7812-808c-703f9de7b9af`) explicitly selected this repository as
the preferred scientific implementation. Current workflow-manager README and
AGENTS.md still name it as authoritative. The accessible Codex task index,
local task metadata (including archived tasks), and related workflow-manager
files did not reveal a newer replacement. This is not a claim to have searched
every historical ChatGPT message: the available task listing is limited and
there is no global ChatGPT message-search connector available here.

The September 4 task retrieving Firebird PDFs has local examples in
`/Users/New/Documents/Codex/2026-09-04/find/outputs/firebird_fight_pdfs/`.
The inspected July 22 report uses an older five-page layout with sustained onset,
interpolation, and turtled-like overlays. Its recent retrieval date does not
make that implementation newer than v0.8.1. The baseline above is chosen using
your explicit source decision and current code, not report modification dates.

## Run

Use the existing environment from the repository root:

```sh
venv-mac/bin/python six_beetle_processor.py \
  --trajectory /absolute/session/trajectories/validated.npy \
  --session /absolute/session \
  --start 62 --window 7200 \
  --video original_video.mp4 --cell-label A1 \
  --output /absolute/new_output_directory
```

Input must contain exactly six trajectories in the existing loader's supported
NPY, H5, or CSV layouts. `session.json` must contain exactly four polygons in
`roi_list`: arena, fungus 1, fungus 2, fungus 3. Coordinates must use the same
coordinate system. ROI numbering reflects input order, not inferred biology.
Use the reviewed validated/without-gaps source when available; the manifest
records the explicitly selected source. The program does not discover or
approve IDtracker runs.

Defaults retained: 30-pixel wake threshold, 30-pixel wall and inward fungus
buffers, 60-pixel social proximity, and rejection of steps strictly above
200 pixels. Frames are global and the end is inclusive (`start + window`).

## Output and interpretation

Each complete new output directory contains:

- `animals.csv`: six rows with exact-start baseline, wake crossing, latency,
  and warnings; IDs 0–5 are trajectory identities, not biological library IDs.
- `windows.csv`: 18 rows: full interval, individual wake-through-end, and a
  shared 3600-interval comparison for each beetle. Unavailable windows have an
  explicit status and blank metrics.
- `regions.csv`: one row per animal, available window, and named region;
  centroid frame counts and midpoint-assigned accepted movement distances.
  Each fungus has whole, inward edge-buffer, and interior rows. Union fungus
  and off-fungus summaries do not double-count overlapping fungi.
- `pairs.csv`: 15 full-window rows, plus 15 fixed-window rows when available;
  jointly observed frames, proximity, contiguous proximity bouts, visible
  returns, and disappearance candidates for every pair.
- `events.csv`: global inclusive intervals for proximity and disappearance
  candidates; overlapping pair events remain separate. Multi-partner
  disappearance is explicitly marked ambiguous.
- `report.pdf`: missing-data summary, all-six map, individual maps, and
  a timeline showing all 15 pairwise proximity sequences.
- `manifest.json`: settings, actual ROI vertices, input and code SHA-256,
  output SHA-256, source paths, versions, video/cell, and `UNREVIEWED` status.

Read [SIX_BEETLE_METHODS.html](SIX_BEETLE_METHODS.html) for calculations and
output-field definitions. Empty numeric values are not zero.

## Deliberate group adaptations and remaining review

The fixed comparison begins at the **latest reliable wake among all six**.
If even one wake is unavailable, the shared comparison is unavailable for all.
This extends the old two-beetle rule and needs biological review before use.
The full and individual post-wake summaries remain available independently.

Social contact is a candidate inference. Proximity does not prove an attack;
missingness does not establish which animal is interacting. Pairwise events
can overlap, so adding their durations is not a measure of elapsed group time.
Individual any-partner duration uses a union, counting each frame once.

The previous optional partner-centroid substitution is deliberately not
exposed in this first group version. Missing coordinates remain missing even
with a single candidate partner. The two-animal LEFT/RIGHT convention is also
not imposed on six animals; exact-start x/y coordinates are retained instead.

This first version does not integrate the existing GUI, remote SLURM batch
submission, or approval/export schemas. Do not feed its CSVs into the old
165-column combiner. No real six-beetle session was supplied or validated in
this task. Verify ROI geometry, identities, threshold suitability, and reports
on a real reviewed session before statistical use. Polygon self-intersection
and containment are not automatically validated; view the report geometry.

## Reproducible synthetic validation

```sh
MPLCONFIGDIR=/private/tmp/six-beetle-mpl venv-mac/bin/python -m unittest discover -s tests -v
MPLCONFIGDIR=/private/tmp/six-beetle-mpl venv-mac/bin/python examples/make_six_beetle_demo.py results/new_synthetic_demo
```

The demonstration is synthetic and clearly labeled. It includes all six
trajectories, three fungi, simultaneous proximity, ambiguous disappearance,
missing coordinates, and a rejected jump. Output directories are never
reused or overwritten. Generated research/demo files remain Git-ignored.
