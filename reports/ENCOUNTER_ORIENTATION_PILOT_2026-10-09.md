# Beetle approach, departure, and body-axis pilot — 9 October 2026

**Codex / AI-authored synthesis and implementation. COMPLETE_UNREVIEWED.**
VAF requested visualizations on good-quality dyadic and six-beetle recordings.
This separate development pilot uses two recordings of each type, with existing
tracking and existing review videos. Production PSC, BA, and the paused identity
editor were not changed. No anatomical head detector was trained.

## Open and interpret the result

[Open the portable collection](../outputs/encounter_orientation_pilot_20261009/review_set/START_HERE.html).
Each page has synchronized movement arrows, undirected silhouette axes,
pair selection, distance and radial-movement graphs, frame stepping, and
proximity-bout navigation. Motion windows cover 0.20, 0.40, and 0.80 seconds.
An optional diamond indicates the motion-aligned end, explicitly assuming
forward travel; it does not establish head direction.

Start with **Six Beetle 1, IDs 3 and 5, bout 1 (global 3294–3344)**.
The geometric estimate attributes approach to ID 5; departure is censored
by missing tracking. **Dyadic 2, bout 1 (1940–1957)** attributes the preceding
one-second approach contribution to ID 1 and subsequent separation to both.
These are hypotheses for video review, not human-confirmed behavior.

## Selection and results

Selection favored low missingness among cases with zero recorded adjacent-frame
jumps over 100 pixels, using existing QC records. Each chosen cell comes from a
different recording. The known WRONG dyadic recording was excluded because of
the unresolved identity-swap report. This is a selected feasibility sample;
absence of jump warnings does not validate identity.

| Viewer | Recording/cell | Raw missing | Body-axis coverage | Motion coverage (0.40 s) | Proximity bouts | Stable approaches / departures |
|---|---|---:|---:|---:|---:|---:|
| Dyadic 1 | Camera 1, 2026-07-02 15:35, Fight ACT2 A2 | 1.46% | 40.40% | 66.58% | 14 | 0 / 0 |
| Dyadic 2 | Camera 1, 2026-07-02 13:10, Fight ACT1 A2 | 1.94% | 51.32% | 76.44% | 24 | 1 / 1 |
| Six Beetle 1 | groupagetrial01_062024_Box02_MIX | 5.40% | 82.79% | 85.26% | 20 | 5 / 4 |
| Six Beetle 2 | groupagetrial06_062224_Box2_OLD | 14.69% | 51.44% | 71.63% | 27 | 3 / 2 |

Coverage denominators are animal-frames. “Stable” means identical A/B/Both
attribution across all three motion windows, not validated accuracy. Totals
are 85 proximity bouts, 9 stable approach and 7 stable departure attributions;
the latter two counts can refer to the same bout. The first dyadic video's lack
of stable attributions is retained rather than selecting a replacement based
on the desired result. The relatively round dyadic silhouettes also limit
body-axis coverage under the chosen elongation threshold.

The four full videos comprise 18 minutes: two 7,200-frame dyadic videos and
two 9,000-frame six-beetle videos, all at 30 fps. Sample frames were visually
inspected, not every frame or identity throughout each video.

## Measurement choices and limitations

All positions come from the frozen raw trajectory arrays. PSC-borrowed
positions are never used. Velocity is a centered least-squares slope over
7/13/25 observations. Every observation must have a unique individual blob
matching the centroid within 5 pixels, and all adjacent steps must be ≤20
pixels. Gaps and unsupported observations are not interpolated. Centered
windows are retrospective and cannot establish response latency.

Silhouette moments supply an undirected axis when the square-root eigenvalue
ratio is ≥1.4; endpoints are 5th/95th percentile contour projections. Shared
blobs and round/degenerate silhouettes have no axis. Anatomical accuracy has
not been scored. Source manifests say IDTRACKER_RAW_NPY, which is an upstream
array designation, not a guarantee against all upstream position estimation.

Proximity bouts use ≤60 original-image pixels for ≥15 contiguous frames.
Bouts are not merged across gaps or threshold excursions, so biological
encounters may be fragmented. Entry/exit beside missing coordinates are
censored. Approach/departure attribution summarizes the preceding/following
one second, requiring ≥70% jointly supported measurements. A contribution
and the net closing/separation must exceed 5 px/s. These are exploratory
thresholds, not production defaults or independently validated rules.

The main limitation is coverage around contact: even low raw missingness can
coexist with inadequate independent silhouettes or velocity windows. The next
step is human scoring of these examples and held-out encounters, evaluating
both attribution accuracy and abstention. Backward walking, pushing, identity
swaps, and camera motion remain separate concerns.

## Evidence and verification

Local root: `outputs/encounter_orientation_pilot_20261009/`.
Firebird root:
`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/encounter_orientation_pilot_20261009/`.
The `review_set/` contains full videos, embedded-data viewers, frame and event
CSVs, unrounded NPZ arrays, methods, source hashes, and receipts.

Seven focused tests passed: velocity units/frame alignment, unsupported-window
and jump masking, radial signs and summed closing speed, departure attribution,
unknown versus stationary, zero-distance handling, and inclusive/censored events.
All four MP4 encoded frame counts and source-video byte hashes passed; original
analysis and blob hashes were verified unchanged during extraction. Local HTML
links passed. Browser playback was checked in all four pages; frame stepping,
motion-window selection, the motion-aligned-end warning, pair switching, and
automatic stopping after selected bout context were exercised. These checks
establish software/package behavior, not biological validity.

Implementation: `encounter_orientation_pilot.py`,
`encounter_orientation_review.html`, `encounter_orientation_methods.html`,
and `tests/test_encounter_orientation_pilot.py`. No source trajectories or
previous release files were edited.
