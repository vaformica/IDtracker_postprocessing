# BA turtling: results of the fresh boundary test

All nine VAF decisions are complete. The revised 0.4 detector improves on 0.3 in this test, but the injury-noted beetle still produces a false event and the earlier-run follow-up still starts too late. Keep it as a marked review aid; these results do not establish reliable unattended turtling totals.

| Clip | Review | VAF on-back frames | 0.4 on-back flags | Extra | Missed |
| --- | --- | --- | --- | ---: | ---: |
| 1 | blind | None | None | 0 | 0 |
| 2 | blind | None | 3307–3435 | 129 | 0 |
| 3 | blind | 5936–6358 | 5936–6375 | 17 | 0 |
| 4 | blind | None | None | 0 | 0 |
| 5 | guided | 4920–5519 | 4920–5519 | 0 | 0 |
| 6 | guided | 7122–8021 | 7122–8021 | 0 | 0 |
| 7 | guided | 6945–7844 | 6945–7844 | 0 | 0 |
| 8 | blind | None | None | 0 | 0 |
| 9 | Earlier follow-up | 6600–7499 | 6910–7499 | 0 | 310 |

## Fresh-cell result

Across the eight fresh clips, 0.4 has 146 disagreements among 13,117 displayed frames (1.11%), versus 178 (1.36%) for 0.3. All 146 are extra flags; none of the 2,823 human-positive frames are missed. Six of these eight clips match completely. The five hidden-prediction clips have 146 / 10,417 disagreements (1.40%); the three guided clips have zero / 2,700. Guided acceptance is not blind validation.

## The injury-noted beetle

In Clip 2, VAF reports a broken leg and no turtling. The new detector falsely flags 3307–3435 (129 frames, 4.30 seconds), versus 139 false frames before. Although the total improves, the changed boundary adds 21 false frames and removes 31. VAF’s recommendation to exclude this animal from training is preserved as a review note. No training or automatic exclusion was performed. The primary result retains this case. As a post-hoc sensitivity check only, the other seven fresh clips have 17 / 12,217 disagreements (0.14%).

## The remaining fresh boundary error

Clip 3 is on its back through frame 6358. Version 0.4 continues through 6375, adding 17 frames (0.57 seconds). Version 0.3 continued through 6397, so the revision removes 22 extra frames. The event is already present at the clip start, 5936; this does not establish its true onset.

## The separate earlier-run follow-up

Clip 9 is scored on-back throughout 6600–7499. Version 0.4 begins at 6910, missing 6600–6909: 310 frames (10.33 seconds), versus 610 missed frames for 0.3. Its 6910 boundary is the preset backward-search limit, not a detected flip. The true onset is at or before 6600 and remains unknown. This follow-up is not part of the fresh-cell accuracy result. Its 7060–7499 portion overlaps earlier scoring; the 460 newly reviewed frames are 6600–7059. Of those, 150 are detected and 310 missed. The 440 overlapping frames match the current detector and are not added again to earlier results.

## Tracking and interpretation

One fresh displayed frame lacks coordinates: Clip 1, global frame 6863. That is 0.0076% of fresh displayed frames (0.0139% of Clip 1). VAF labels it non-turtling, and the detector has no flag; this agreement does not convert unknown tracking into an automatic upright classification. Restricting the fresh comparison to the 13,116 coordinate-known frames gives the same 146 errors (1.1131%). Tracking availability does not establish posture. There are no tracking-missing positive frames in this round. Flailing was not assessed.

## What this check supports

The rejected-loop scene, random control and preselected complete run match the human no-turtling scores. The three guided scenes match the supplied on-back intervals, including the scene selected for low centroid motion; this does not separately establish that the animal stopped flailing. Predictions were frozen before these scores. Cells are new, but their source recordings were previously represented. Targeted clips and correlated frames do not estimate population accuracy or independent biological sample size. All-nine descriptive disagreement is 456 / 14,017 (3.25%), down from 788 (5.62%); this mixes fresh footage and a calibration follow-up and must not replace the separate results.

## Next useful refinement

Prioritize starts that reach the backward-search cap: mark their onset as unresolved and review earlier footage rather than treating the cap as a true flip. Retain the injury case as an explicitly identified challenge/QC case and establish any training-exclusion policy before fitting another version. Check the remaining righting boundary with adjacent footage before changing its rule. No threshold retuning, new tracking, production integration or broad release was performed in this score-import task.

## Preservation and verification

The original JSON is preserved byte-for-byte with its SHA-256. The scoring-set identity, all nine clip bounds/modes, explicit completeness, intervals and saved state were checked against the frozen package. Queue predictions were checked against their full-run masks and prior hashes. A second interval-set calculation independently checked all confusion-matrix counts. Human labels apply only to displayed frames; prior predictions, source files and earlier reports remain unchanged.

Evidence: `outputs/ba_boundary_validation_results_20261007/` locally and `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_boundary_validation_results_20261007/` on Firebird.

Source score SHA-256: `a5e268507b6385651ec06cdcbe0e6783ebb1dcd4186adec4a23a91bfd6de393a`.

The earlier development report remains a historical pre-score record. This report is the current interpretation of the nine-clip test.
