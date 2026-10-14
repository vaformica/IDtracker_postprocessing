# BA turtling: twelve complete runs scored, 6 October 2026

The full-run review exposed a substantial duration error that the earlier short clips did not reveal. The detector correctly left all seven reviewer-confirmed negative runs unflagged, and its eight random runs matched closely. However, targeted Run 1 contains 86.17 seconds of reviewer-marked turtling that the detector missed. **Keep the detector experimental; these results do not support treating its automatic duration as the final time turtled.**

VAF returned three JSON files with five positive runs explicitly scored. Runs 3, 4, 5, 7, 9, 10 and 11 were blank in the files; Vince then confirmed that all seven had no turtling or flailing. The original uploads are preserved byte-for-byte. A separate attributed clarification supplies those negatives, and corrected copies of each part now contain four complete annotations. No blank entry was treated as a negative before that clarification.

## What the frozen experimental detector found

| Run | Selection | Human turtled time | Automatic candidate time | Missed turtled time | Extra candidate time |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | Targeted challenge | 182.03 s | 103.10 s | 86.17 s | 7.23 s |
| 2 | Random | 73.43 s | 75.17 s | 0.00 s | 1.73 s |
| 6 | Targeted challenge | 188.40 s | 186.50 s | 1.90 s | 0.00 s |
| 8 | Random | 93.00 s | 93.00 s | 0.00 s | 0.00 s |
| 12 | Targeted challenge | 92.53 s | 98.77 s | 0.00 s | 6.23 s |

Runs 3, 4, 5, 7, 9, 10 and 11 have zero human turtled time and zero candidate time. Missed and extra time are reported separately because they can cancel in a total-duration comparison. For example, Run 1 is undercounted by 78.93 seconds overall, but actually has 86.17 seconds missed plus 7.23 seconds falsely added.

## Random runs and targeted challenges are separate evidence

The **eight random runs** cover eight previously unscored source recordings and contain two positive runs. Both the original baseline and the experimental rule detect all 4,993 human-positive frames (166.43 seconds) and add 52 false-positive frames (1.73 seconds), all in Run 2. Their predictions are identical in this subset. Six of these runs are confirmed negatives.

The **four targeted runs** include three positive runs and one negative. They share four of the random subset’s source recordings and were deliberately selected to challenge the rules. The experimental rule detects 80.98% of their human-positive frames; 2,642 frames (88.07 seconds) are missed and 404 frames (13.47 seconds) are falsely added. These are descriptive results for this sample, not population accuracy or independent-frame observations.

Across all twelve runs, the human annotation contains 629.40 seconds turtled. Experimental candidates total 556.53 seconds: 88.07 seconds are missed and 15.20 seconds are falsely added. The pooled 86.01% positive-frame sensitivity is only a descriptive summary of this enriched collection. It must not replace the random/targeted separation.

## What the additional labels taught us

Run 1 is annotated as continuously turtled and flailing from frame 2834 through 8294. The detector fragments that interval into repeated short candidates, with missed stretches as long as 19.27 seconds. These misses occur during **annotated flailing**, so the remaining problem cannot be attributed only to quiet periods on the back. The result shows that tight centroid looping is not a reliable duration measure for this example; the cause of the absent trajectory evidence still needs inspection.

Run 6 has one explicitly quiet-on-back interval: frames **7331–7399**, 69 frames or **2.30 seconds**. The baseline detects 60 of those frames; the experimental continuity rule detects all 69. This supports that local gap correction. The same rule also repairs a 12-frame gap during annotated flailing (6694–6705), for 21 recovered frames in total. It still misses the final 57 frames (1.90 seconds) of Run 6 despite the continued turtled annotation.

The experimental onset extension in Run 1 adds frames **1109–1176**, all outside the human turtling annotation: **68 additional false-positive frames (2.27 seconds)**. The baseline already had a false candidate immediately afterward. Thus the extension lengthens an incorrect event here. Across these twelve runs, the experimental change recovers 0.70 seconds of true turtling but adds 2.27 seconds of false candidate time. It should not be promoted as a uniformly better rule.

## Next development step

No further broad scoring round is needed before investigating these errors. Inspect Run 1’s false event at 1109–1325 and its long missed stretches (especially 3177–3723 and 4936–5513), together with Run 6’s final 8186–8242 segment. Compare image posture with centroid movement and tracking quality, then develop evidence for maintaining an overturned episode and recognizing recovery. Simply lengthening all gap joins would risk extending false events such as the one already seen in Run 1.

The present rules remain frozen at 0.1.0-experimental; no thresholds or automatic videos/PDFs were changed after seeing these scores. Any rules revised using these annotations will make this set development evidence, requiring a later independent test. Human-confirmed durations can be shown separately in reviewed outputs, with attribution. Right-censored intervals ending at the last video frame are not observed recoveries.

## Evidence and verification

Local folder: `outputs/ba_turtling_fullrun12_results_20261006/`. Firebird destination: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_fullrun12_results_20261006`. It contains the three unchanged uploads, clarification, corrected exports, frozen prediction snapshots, comparison with frame counts and error intervals, source receipts and reproducible evaluator. The evaluator verifies uploaded set IDs and public-clip hashes, all frame bounds, matching raw decisions and parsed intervals, unchanged prediction hashes, inclusive frame accounting, and that flailing is contained within annotated turtling.

Status: **TWELVE_RUN_COMPARISON_COMPLETE_DETECTOR_REMAINS_EXPERIMENTAL**. Software accounting is checked; the human labels are attributed observations, and the detector remains a review aid rather than a validated automatic duration measure.
