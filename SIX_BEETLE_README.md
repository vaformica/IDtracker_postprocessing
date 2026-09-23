## Persistent detection-supported analysis (v0.7.0)

For the reusable two-or-more-animal command and input contract, see
[GROUP_PIPELINE_README.md](GROUP_PIPELINE_README.md).

All group-analysis CLI runs use the same persistent group model by default. The
recommended pipeline command exports real detection evidence with the session's
IDtracker environment, runs the v0.7.0 analysis, and creates a portable
synchronized HTML/video review from the same canonical state bundle:

```sh
venv-mac/bin/python run_six_beetle_pipeline.py \
  --session /path/to/session \
  --source-video /path/to/original.mp4 \
  --analysis-output /new/run/analysis \
  --review-output /new/run/review \
  --start 422 --end 7622 --fps 30 --label Box01
```

The source session remains read-only: when no matching `blob_evidence.json`
already exists, the export is written beside the new analysis directory. Do not
delete `preprocessing/list_of_blobs.pickle`; it is the detection evidence needed
for persistent piles. New sweep packages automatically include and invoke this
complete pipeline.

For a different group size, use the same options with `run_group_pipeline.py`.
It reads the number of animals from the trajectory array and the number of
fungi from the session ROI list (arena first, then one or more fungi). The
processor, CSV, PDF, and synchronized review all use those counts. For an
analysis-only run, `group_processor.py --help` shows the direct entry point.
The current Firebird discovery GUI is deliberately limited to the six-beetle,
four-ROI project; the general command-line pipeline is the reusable interface
for dyads and larger groups. Tests cover two animals/one fungus, the established
six/three profile, and seven animals/four fungi. Identity and pile results for
new experimental designs still require video QC before scientific use.

Canonical positions in `canonical_states.npz` and `canonical_positions.csv` drive estimated report metrics and `build_canonical_review.py`. Original-coordinate control tables remain separate. Assigned beetles within 60 pixels remain proximity interactions; PSCP requires at least one inferred identity in a shared detected blob. Persistent membership does not imply a known position: no supporting detection means missing. Model outputs remain UNREVIEWED; tested recovery of the 4–5 pile does not validate every identity. See [validation and limitations](reports/PERSISTENT_GROUPS_2026-09-21.md).

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

## Local Firebird GUI

Launch the dedicated six-beetle GUI on the Mac:

```sh
venv-mac/bin/python six_beetle_firebird_gui.py
```

The GUI defaults to the established `firebird` SSH alias and
`~/.ssh/id_ed25519_firebird`, matching the dyadic post-processing GUI and other
Firebird tools. The alias supplies `HostName firebird.swarthmore.edu`, user
`vformic1-swat`, and `IdentitiesOnly yes` from `~/.ssh/config`. Connect Cisco
Secure Client to the Swarthmore VPN before using **Test SSH**.

It searches one or more Firebird roots over read-only SSH for sessions with six
animals and four ROIs, lets the researcher inspect or edit the selected session,
trajectory, source video, inclusive frame range, proximity distance, jump
thresholds, movement threshold, and ROI buffers, previews the exact command,
uploads an immutable code snapshot, and submits a Slurm post-processing job.
The download action packages the PDF, CSVs, manifest, interactive HTML, and MP4
and verifies the archive SHA-256 after transfer. Jobs write only under the
configured output root. They never approve results automatically.

This is an explicit **six-beetle persistent-piles** profile. The existing
`firebird_gui.py` and processor v0.8.1 remain the supported dyadic path. Animal
counts above six are not yet supported by the six-beetle report layer, even
though the lower-level persistent-group model is written for an arbitrary
number of identities.

## Analysis-only command

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
coordinate system. Fungus ROIs are numbered left to right; Vince describes fungus ROI 1 as the leftmost or bottommost fungus bracket. The arena is ROI 0. The script preserves this supplied order and does not automatically sort polygons.
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
- `<TOML stem>.pdf`: missing-data summary, all-six map, full-page individual maps, 3D trajectories, fungus table, and
  a timeline showing all 15 pairwise proximity sequences, and an additional three-color per-frame identity/contact timeline.
- `frame_states.csv`: every global frame and animal, with the display state,
  coordinate presence, nearby-partner count, disappearance-candidate status,
  and ambiguous-attribution flag.
- `frame_data.csv`: one row for each beetle at each global frame, joining raw
  and canonical coordinates, evidence source, fungus membership, visible
  proximity partners, PSCP partners, and accepted movement-step allocation.
  For a later inclusive subwindow, run
  `python frame_data.py BUNDLE --start FIRST --end LAST --output NEW_FOLDER`.
  This recalculates per-beetle fungus frames, percentages, distances, and
  pairwise proximity/PSCP frame counts without rerunning tracking. The selected
  first frame's incoming movement step is excluded. The command checks the
  frame CSV against the source manifest and never overwrites the original.
  For older canonical bundles, first run
  `python backfill_frame_data.py OLD_BUNDLE NEW_FOLDER`; this creates a separate
  verified export without altering the older bundle.

The three existing Trial 01 bundles have separate backfilled exports under
`results/frame_data_v062/Box01_OLD`, `Box01_OLD_TEst`, and `Box02_MIX`.
Their full-window recalculations reproduce the saved canonical fungus frame,
fungus distance, proximity, and PSCP totals for every beetle and pair.
- `manifest.json`: settings, actual ROI vertices, input and code SHA-256,
  output SHA-256, source paths, versions, video/cell, and `UNREVIEWED` status.

Read [SIX_BEETLE_METHODS.html](SIX_BEETLE_METHODS.html) for calculations and
output-field definitions. Empty numeric values are not zero.

The methods page describes the current scientific behavior rather than serving
as a version-history appendix. Changes to pile membership, proximity,
missingness, movement, spatial allocation, output fields, or report
interpretation must update that page in the same commit. A regression test
checks the documented processor, base, and persistent-model versions against
the code.

## Deliberate group adaptations and remaining review

The fixed comparison begins at the **latest reliable wake among all six**.
If even one wake is unavailable, the shared comparison is unavailable for all.
This extends the old two-beetle rule and needs biological review before use.
The full and individual post-wake summaries remain available independently.

Social contact is a candidate inference. Proximity does not prove an attack;
missingness does not establish which animal is interacting. Pairwise events
can overlap, so adding their durations is not a measure of elapsed group time.
Individual any-partner duration uses a union, counting each frame once.

The two-animal LEFT/RIGHT convention is not imposed on six animals; exact-start
x/y coordinates are retained instead. Do not feed the six-beetle CSVs into the
old 165-column dyadic combiner. The three real trial01 sessions have been run,
and targeted intervals motivated the current pile rules, but the automatic
outputs remain `UNREVIEWED`. Verify ROI geometry, identities, threshold
suitability, and report/video agreement before statistical use. Polygon
self-intersection and containment are not automatically validated; view the
report geometry.

## Reproducible synthetic validation

```sh
MPLCONFIGDIR=/private/tmp/six-beetle-mpl venv-mac/bin/python -m unittest discover -s tests -v
MPLCONFIGDIR=/private/tmp/six-beetle-mpl venv-mac/bin/python examples/make_six_beetle_demo.py results/new_synthetic_demo
```

The demonstration is synthetic and clearly labeled. It includes all six
trajectories, three fungi, simultaneous proximity, ambiguous disappearance,
missing coordinates, and a rejected jump. Output directories are never
reused or overwritten. Generated research/demo files remain Git-ignored.

## Per-frame timeline (v0.2.0-six-beetle)

The existing pair-proximity plot is retained. A sixth PDF page shows all six
identities over the inclusive global-frame window: blue = observed/ID assigned,
orange = missing, gold = presumed social contact. Gold takes precedence when
there is observed proximity or participation (missing animal or visible
partner) in a qualifying bounded disappearance candidate. Ambiguous
multi-partner candidates are hatched; they are not silently assigned to one
partner. Coordinate presence remains a separate field, so gold never changes
missing-data counts or fills trajectories. Observed means present in the
selected trajectory source; pre-existing IDtracker gap filling is not evidence
that the animal was visible in the original video. Every frame is exported
even when a short event is narrower than a pixel in the full-window plot.

### Pair-specific presumed contact (v0.2.1-six-beetle)

The 15-pair chart now overlays qualifying disappearance intervals in gold,
while observed proximity remains teal. Hatching marks ambiguous candidate
partners. Inference comes from each exact pair's full-window disappearance
events in events.csv, never from intersecting two individual contact states.
A blank interval means no observed proximity or qualifying disappearance
evidence; it does not establish that the animals were not in contact.

### Version 0.3.0 reports

The PDF now includes one full-page trace per beetle, orange X markers at the last
assigned coordinate before each missing run, an X/Y/time 3D trajectory page, and
a six-row fungus occupancy/distance table. The original pairwise and individual
state timelines are retained. `fungus_summary.csv` preserves exact frame counts
and distances in pixels. Distance uses the existing accepted-step midpoint rule.
There are 12 PDF pages in this historical version; current six-animal reports
contain 13 pages.

PDF names default to `<video stem>_<cell label>.pdf`; `--pdf-name <TOML stem>.pdf`
sets an exact TOML-derived name. Existing output folders are never overwritten.

### Version 0.4.0: presumed social disappearance

This supersedes the v0.3.0 no-substitution display. If a beetle disappears after
being within the proximity threshold of a unique remaining visible beetle in
the preceding frame, its estimated location follows that visible anchor. An
existing group can absorb another disappearance or transfer to a new anchor;
all group members then share the remaining visible beetle's location. IDs that
reappear resume their own measured coordinates. No visible anchor, or multiple
possible anchors, leaves the missing position unresolved. No future return is
required. Inference starts before the analysis window to carry established
groups into it.

`presumed_positions.csv` retains raw x/y, estimated x/y, inference flags, visible
anchor IDs (-1 unresolved), and ambiguity for every beetle/frame. Original
windows/regions/fungus tables retain raw-coordinate metrics; `estimated_*` tables
include presumed positions, with identical window boundaries and wake anchors.
Original missing-coordinate percentages remain raw. Original bounded pair
candidates are retained in `legacy_events.csv` for provenance, not used for the
new display. Gold in the individual timeline now means presumed social
disappearance, including the group's visible anchor; proximity alone remains
observed. Pair timelines retain teal observed proximity and gold group membership.

The 13-page PDF uses solid raw traces and dashed presumed positions in both 2D
and 3D, and includes separate observed and estimated fungus tables. Distances
and times attributed to presumed positions are model-based estimates.

### Version 0.4.2: frames only

All occupancy times are integer coordinate-frame counts, and the 3D time axis
uses global frames. Seconds are not calculated or exported. This supersedes
the earlier FPS-conversion instructions; optional FPS is source metadata only.
