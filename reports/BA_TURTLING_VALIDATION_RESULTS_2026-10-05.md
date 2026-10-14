# BA turtling validation scores received, 5 October 2026

## Current result: all seven annotations complete

Vince clarified that clip 5 becomes turtled at global frame **3364** and remains turtled through the clip's final frame, **3723**, and then confirmed active flailing over that interval. This is 360 inclusive frames, or **12 seconds at 30 fps**. The recovery was not observed within this clip. The original upload remains unchanged; separate attributed messages and a corrected export record both behaviors. This clarification supersedes the pending status below.

The frozen experimental detector agrees with the posture annotations on all seven clips (3,240 frames, 108 seconds). In the six clips from previously unscored recordings, both detectors have 840 true-positive and 2,040 true-negative frames, with no missed or false-positive frames. In the separate development clip, the experimental rule recovers the baseline's 18 missed frames (0.6 seconds). No thresholds or pipeline code were changed for this comparison.

These are encouraging results from a small, selected sample, not a population accuracy estimate. Positive new-source clips 5 and 6 come from the same recording and likely the same prolonged episode; they are not independent positive events. The experimental rule's additional benefit remains demonstrated on an earlier development source. Active-flailing labels are preserved, but this comparison evaluates automatic **posture** candidates, not an automatic flailing classifier. The detector remains experimental; additional independent onsets, recovery boundaries and long stationary periods are the next useful validation targets.

Completed evidence: `outputs/ba_turtling_validation_completed_20261005/`, mirrored to `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_validation_completed_20261005`. It contains the unchanged upload, attributed clarification, corrected scores, frozen prediction snapshots, per-clip comparison, reproducible evaluator and checksum receipt. Earlier partial evidence remains intact.

## Historical intake and partial comparison

VAF's uploaded `BA_turtling_validation_scores_20261005.json` contains **all seven entries**. Clip 7 is explicitly `none` for both posture and flailing, marked complete, and agrees with Vince's accompanying message that the last clip had no turtling. The upload remains byte-for-byte unchanged in `outputs/ba_turtling_validation_results_20261005/scores_original.json`. The accompanying message is preserved separately.

The file reports six completed clips because **clip 5 is incomplete**: `posture_ranges` is `3373`, while `flailing_ranges` is `3723`. The form requires start-end ranges within each behavior field. Those values might be the beginning and end of one bout, but that interpretation requires Vince's clarification; neither the evaluator nor repaired UI guesses it. Clip 5 is excluded from current metrics. Both frozen detectors mark 3364-3723 for that clip; do not compare that boundary against an unconfirmed interpretation of the entry.

## Partial comparison with frozen rules

| Assessment group | Included clips | Reviewed duration | Prototype misses | Experimental misses | False-positive frames |
| --- | --- | --- | --- | --- | --- |
| New source recordings | 01, 02, 04, 06, 07 | 80 s | 0 | 0 | 0 for both |
| Earlier-source development pause check | 03 | 12 s | 18 frames (0.6 s) | 0 | 0 for both |

The new-source subset has 480 confirmed positive and 1,920 confirmed negative frames. Both detectors agree with these complete labels. The additional pause is now human-confirmed as turtled, so the continuity rule recovers its 18 missed frames. Clip 03 also has an active-flailing-throughout label; the computational evidence label `quiet_pause_hypothesis` describes weak centroid evidence and must not be interpreted as an observed cessation of flailing.

This is an enriched, small sample with one new-source positive complete clip and another onset clip awaiting clarification. It is not a population accuracy estimate or enough evidence to promote the experimental rule. No detector thresholds were changed using these scores. Full source-video evaluation, recovery boundaries and longer quiet periods remain unresolved.

## Scorer repair

The file proves the last clip was saved. The exact reported navigation problem was not reproduced; the incomplete-count presentation was misleading. Reusable `ba_turtling_scoring_template.html` version 0.2.0 adds explicit Save this clip and Download scores controls at the top; the final Next control becomes Finish & download. Both selection-change and input events save, the page identifies WHICH clips need attention, and invalid interval messages request both endpoints. Partial downloads retain all raw entries. A separate browser-storage key preserves the old scorer state.

The repaired standalone page preloads all uploaded entries and opens at the first incomplete clip. It changes no annotations and does not require complete clips to be rescored. `tests/test_ba_turtling_scorer.cjs` verifies last-clip negative scoring without navigation, finish/download, detection of malformed earlier intervals, per-clip persistence, frame marking and export. These are programmatic behavior checks, not a fresh native-browser playback verification.

Current status: **PARTIAL_EVALUATION_PENDING_CLIP_05_CLARIFICATION**. Evidence is in `outputs/ba_turtling_validation_results_20261005/`. The new remote root is `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_validation_results_20261005`; original scoring-set receipts and human-upload bytes remain separate.
