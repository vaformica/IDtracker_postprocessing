# BA review priorities and manual flags

The BA review dashboard now covers all **121 existing analysis windows**: the 100-run pilot, its separate earlier-source follow-up, and the 20-cell boundary-test cohort. Each window contains 7,200 inclusive frames; together they represent 14 recordings. No new tracking or detector fit was needed. Frozen 0.4 turtling predictions and original coordinates remain unchanged.

Open `Downloads/BA_review_priorities_20261012/START_HERE.html`. The dashboard lets VAF filter or sort runs, inspect reasons and global-frame ranges, select **Needs video review**, and add a reason and notes. **Download my review flags** exports `BA_review_flags_20261012.json`; the same file can restore those flags in another browser. These requests do not approve or exclude an animal, change posture scores, or remove automatic warnings. Browser storage is convenient but the downloaded JSON is the portable record.

## What needs attention

There are **29 high-priority runs**, **35 with other checks**, and **57 without automatic flags**. The last group still needs spot checks; it is not an approved collection.

| Reason | Runs |
| --- | ---: |
| Missing tracking, including short gaps | 36 |
| Adjacent-coordinate jumps over 100 pixels | 24 |
| Long turtling candidates | 13 |
| Ambiguous circling / short motion anchors | 12 |
| Event boundaries limited by tracking, recovery, or analysis edges | 19 |
| Recorded camera artifacts | 9 |
| Recovery never established | 3 |
| Long inferred continuation | 3 |
| Onset reaches the backward-search limit | 1 |
| Attributed injury note | 1 |

These categories overlap. The injured-beetle flag retains VAF's attribution and recommendation; it does not implement a training or biological exclusion. A displacement across missing frames is recorded separately from a true adjacent-frame jump. Camera artifacts are inherited annotations, not newly detected camera motion.

## Rules and limitations

High priority is triggered by missing tracking at least 5% of the window or a gap of at least 120 frames; at least three adjacent jumps over 100 pixels or any over 200 pixels; candidate turtling in at least 25% of the window or one bout of at least 1,800 frames; a capped onset; unresolved recovery; a recorded camera artifact; or the attributed injury note. These are provisional triage thresholds, not validated exclusion rules. Pixel thresholds apply to original-image coordinates.

Other checks include any smaller missing gap, ambiguous loops, boundaries adjacent to missing coordinates/jumps/recovery or at the analysis limits, at least 300 frames of inferred continuation, disagreement between 0.3 and 0.4, and exact-coordinate plateaus of at least 600 frames. Existing upstream baseline/outside-arena flags remain visible when present.

“Behavior-review evidence” counts the union of ambiguous-loop frames, inferred continuation, and version disagreement. It is **not a confidence probability**, an exhaustive uncertainty measure, or a confirmed turtling duration. In particular, low movement can be quiet overturned posture or upright immobility. Missing coordinates remain unknown. The dashboard shows raw missing percentage, longest gap, jump count and maximum size, candidate frames/percentage, and human scoring coverage separately.

Human annotations cover **82,030 of 871,200 analysis frames**. The previous 60-clip scores and returned nine-clip scores are combined only over their displayed coverage, with overlapping frames counted once and conflicting labels checked. Human on-back counts therefore describe scored portions, not full-run totals unless coverage is complete. The unresolved BA060 onset and the 17-frame righting discrepancy remain as documented in the [boundary-test results](BA_TURTLING_BOUNDARY_VALIDATION_RESULTS_2026-10-07.md).

## Footage and next use

The dashboard includes the already-delivered two-scene boundary review: **6,249 frames, 3.47 minutes**, predictions hidden. It still exports `BA_focused_boundary_scores_20261009.json`; the original scoring-set identity is preserved. VAF is checking the flip while this dashboard is delivered. Those new scores have not been received or applied here.

Existing-footage links identify the clip to select in its earlier scoring round and disclose that round's prediction version. The historical 100-run rounds display 0.2 predictions, not the dashboard's frozen 0.4 mask. Full videos for all 121 runs are not embedded in this dashboard. Runs without a prepared clip can be requested using the manual flag and notes, then assembled into a focused review queue. Expanding to remaining BA TOMLs and regenerating review PDFs/videos with reviewed durations are subsequent stages, not completed by this QC build.

## Evidence and checks

Separate code: `ba_review_priority.py` (`ba-review-priority-0.1.0`), `ba_review_flags.js`, and `ba_review_priority_template.html`. Per-run sidecars, the full index, input hashes, tests, and the delivered pages are under local `outputs/ba_review_priorities_20261012/` and Firebird `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_review_priorities_20261012/`.

Fourteen QC tests passed, covering missing gaps, jump denominators, displacement across gaps, censored boundaries, search caps, unknown tracking, immutable inputs, and invalid settings. Fourteen manual-flag/filter/export checks passed. A script-level dashboard harness checked all 121 rows, filters, search, sorting, manual selection, escaped notes, and export. Sidecar/index agreement, existing footage links, embedded script syntax, and the boundary-review hash were checked. These checks do not establish browser rendering/playback or biological validity.

The interrupted October 9 attempt remains preserved. Firebird build 918303 exposed an assembly bug that treated the separately named historical follow-up as a fresh run; the source-group lookup was corrected. Build **918305 completed all 121 runs**. The detector and input files were not changed. The short-review encoding job **917586** previously completed and its package is reused unchanged.
