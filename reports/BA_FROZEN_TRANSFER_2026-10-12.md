# Frozen BA recovery rules: eight-cell transfer test

AI-written by Codex, 12 October 2026. COMPLETE_UNREVIEWED; no scientific outputs replaced.

Five jump cases and three clean controls were selected before their recovery results.
The eight cells cover five recordings; three recordings were not in the preceding
recovery development sample. These cells have existing tracking and some were used
in earlier BA/turtling work. This is not an unseen-population accuracy estimate.
No new IDtracker runs were started.

The candidate generator and the major-jump (0.2), excursion (0.3), and stationary
reacquisition (0.4) functions were copied and hashed before running. Their thresholds
were not adjusted. A new window-selection policy was also fixed before results:
original >100-pixel edges, 30-frame context, overlapping windows merged, stationary
reacquisition only in windows of at most 180 frames with at least 95% original
coverage. Its internal stationary/image criteria must still pass. Previous excursion
replacements are protected. This eligibility policy is itself being tested, not
previously validated as part of the original hand-selected stationary scenes.

The matched clean controls are BA_058 alongside BA_032 and BA_016 alongside BA_067;
BA_051 adds a further recording. Two control windows were fixed per run; the short
review uses the first fixed window for each clean run plus all eligible jump windows.
The other preselected windows remain recorded for subsequent spot checks. Full
7,200-frame arrays and crop videos are archived for every run.

| Run | Original >100 px steps | Proposed >100 px steps | Positions replaced | Missing frames original → proposed |
|---|---:|---:|---:|---:|
| ba_082 | 11 | 0 | 8 | 38 → 38 |
| ba_059 | 10 | 1 | 10 | 68 → 68 |
| ba_032 | 2 | 0 | 2 | 3 → 3 |
| ba_014 | 2 | 0 | 2 | 9 → 9 |
| ba_067 | 1 | 0 | 1 | 118 → 118 |
| ba_058 | 0 | 0 | 0 | 0 → 0 |
| ba_016 | 0 | 0 | 0 | 0 → 0 |
| ba_051 | 0 | 0 | 0 | 0 → 0 |

The reviewer contains 11 clips and 816 encoded
frames (27.2 seconds at normal speed). Traces are visible
by default, with separate trace and video judgments. Scenes without a replacement
remain in the reviewer rather than being discarded. Missing proposals, if any,
are explicit. A reduction in jumps is not confirmed biological improvement, and
unknown endpoints can remove a jump without locating the animal.

All eight raw arrays match the frozen original baselines exactly. The three clean
controls remain coordinate-for-coordinate unchanged across their full runs. The
57,600 full encoded frames, per-clip frame counts, clip alignment samples,
source/media hashes, frozen implementation hashes and actual viewer scripts were
checked. Browser playback was not tool-tested. Existing scientific analyses,
source videos, TOMLs and archived tracking were not altered.

Expected score export: `BA_frozen_transfer_scores_20261012.json`, schema
`ba-frozen-transfer-review-v1`. Video acceptance covers displayed proposed changes
and explicitly proposed missing observations; controls cover only displayed
proposed tracking. Trace plausibility is never interpreted as correct positions.
Preserve blank/unsure states and optional notes. Await human scoring before any
broad application. Evidence: PLAN.json, ELIGIBILITY_POLICY.json, FROZEN_HASHES.json,
SUMMARY.json, per-run receipts/FINAL_AUDIT.json, REMOTE_VALIDATION.json and
LOCAL_VALIDATION.json in this output root.

Eight representative original/proposed overlay pairs were visually inspected. No thresholds were changed after seeing these outcomes. Compute array 918542 and packaging job 918553 completed.
