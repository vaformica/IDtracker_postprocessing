# BA turtling: better event boundaries, followed by a fresh check

VAF asked for the next refinement and a practical way to test it. A separate **0.4.0-development** experiment improves event boundaries while retaining 0.3.0's quiet-posture continuity and ambiguous-loop review states. Simple image features were also tested, but performed poorly across withheld recordings and were not added to the detector. Original scores, frozen predictions, videos/PDFs and production defaults remain unchanged.

The fresh scorer is `Downloads/BA_boundary_validation_20261007/START_HERE.html`. It contains **nine clips, 7.79 minutes of video**: eight clips from unused cells and one explicitly separate earlier-run follow-up. The user can pause, step through original global frames, mark Start / Stop / Continues to clip end, save No turtling or Unsure, and download `BA_boundary_validation_scores_20261007.json`. Controls remain below the video. Five fresh clips have predictions hidden; the three other fresh clips show 0.4 suggestions. The older-source follow-up also hides predictions.

## What changed

The new module is `ba_turtling_boundary_experiment.py`. It consumes the frozen 0.3 candidate mask, original x/y and unchanged death-feint recovery eligibility. It receives no labels, run identities or manually specified event frames.

**Search backward from a supported event.** The algorithm examines at most 300 preceding frames, using a fixed reference from the first 30 supporting positions. It extends only through observed, recovery-eligible positions within 35 pixels of that reference, with adjacent steps at most 20 pixels. A missing coordinate, jump, spatial departure, previous episode or the search limit stops it. This is an onset-continuation hypothesis, not a detected image of a flip. A search that reaches its limit can still start later than the true event.

**Look for sustained directed departure near the ending.** In the final 120 frames of an existing episode, the algorithm tests 30-position windows for net travel of at least 30 pixels, net/path efficiency of at least 0.85, no missing coordinates and no step above 20 pixels. Five consecutive qualifying windows justify trimming the remaining tail from the first qualifying window. The test uses future observations, so this is an offline analysis rule. Stillness alone never supplies evidence of righting. Righting followed immediately by an upright stationary period remains difficult.

Both changes retain separate per-frame evidence and adjustment intervals. They do not invent coordinates during missing tracking or replace the original wake metric. The 0.3 motion-based circling filter is unchanged.

## Agreement with existing scores

| Reviewed set | 0.3.0 | 0.4.0 |
| --- | ---: | ---: |
| Latest 60 clips: wrong frames | 427 / 68,453 (0.624%) | 26 / 68,453 (0.038%) |
| Latest 60 clips: missed / extra flags | 370 / 57 frames | 3 / 23 frames |
| Earlier 12 full runs: wrong frames | 99 / 86,400 (0.115%) | 54 / 86,400 (0.063%) |
| Earlier five-clip check | 0 / 16,200 | 0 / 16,200 |

The current 60-clip result consists of **three tracking-missing positive frames and 23 extra flags**. It removes all 367 missed positive frames that have coordinates, within the previously scored windows. BA069 now begins at 1626, one frame before VAF's 1627 label. BA026 retains 17 extra ending frames instead of 52. BA016 retains its five extra frames.

For BA060, the new hypothesis reaches **6910**, the 300-frame backward-search limit, while the previous human review began at 7060. Its true onset before 7060 is not established. The final new scoring clip shows 6600-7499 so VAF can assess this extension: 6600-7059 is newly displayed, and 7060-7499 overlaps the prior score. This follow-up must not be counted as independent validation, and overlapping frames must not be double-counted in later evaluation.

The older 12-run result has one newly missed endpoint frame: Run 2's first event is cut at 4122, one frame before its inclusive human endpoint of 4123. That run loses 46 extra flags overall; other older runs are unchanged. The confirmed Run 12 event, Run 1's 2834 onset, quiet tails and seven entirely negative older runs remain intact. The earlier five-clip results are unchanged. The six new-source clips from the older seven-clip validation were not re-evaluated here.

These are **development fits**, not independently measured error rates. Labels already inspected during engineering cannot serve as a clean test of the resulting rules. The original 60-clip selection also includes targeted candidates, negative full runs and a prior follow-up, so its overall frame percentage is not a population estimate.

A diagnostic sensitivity check varied lookback 180/300/450 frames and radius 25/35/45 pixels. With a 25-pixel radius, 137 missed frames remain; with 35 pixels and 180 frames, 40 remain. With 35 or 45 pixels and 300 or 450 frames, the result stays at 23 extra / 3 missing-coordinate frames. The earlier circling filter's documented threshold sensitivity remains unresolved; these boundary checks do not validate that filter.

## Image features: tested and rejected for automatic use

The image experiment used previously scored, frame-verified videos and sampled every sixth frame. A fixed crop around the tracked center supplied local outline and intensity features: component area, shape, elongation, edge strength, contrast and body-versus-surround darkness. Neither frame number, run ID, recording ID nor absolute location was supplied as a predictor. Recording identity was used only to keep each entire recording out of its own training set.

The diagnostic retained **5,938 usable images across 12 recordings**. Another 1,362 sampled frames were not recovery-eligible; 4,109 had an unavailable center or a crop crossing the video edge; seven failed the crop-ring quality check. Thus this test has substantial image-availability limitations, especially near walls.

At a fixed 0.5 decision threshold, leave-one-recording-out logistic regression disagreed with 916 / 5,938 labels (15.43%); a shallow random forest disagreed with 1,729 / 5,938 (29.12%). The existing 0.3 movement detector disagreed with 50 / 5,938 (0.84%) on those exact same sampled frames. These diagnostic image models therefore were **not combined with or substituted for the detector**. This does not show that richer video-based posture analysis cannot work; it shows that these simple features are insufficient here. No image-model predictions enter the fresh scorer.

## The fresh review

Twenty unused cells were selected before new predictions with seed **202610073**, cycling across ten eligible source recordings after shuffling recordings and cells. The remaining eligible pool had 61 unused cells, all from previously represented recordings. This is a new-cell test, not a new-recording holdout. No new IDtracker jobs were needed; matching existing tracking was reused. No selected failure was replaced, and all 20 analyses completed.

The code was frozen and hashed before applying 0.4 to the new cells. Clip-selection seed is **202610074**. The final queue contains:

- One complete run selected before predictions, with suggestions hidden.
- Two short 0.3-versus-0.4 disagreement scenes, with suggestions hidden.
- One rejected-loop scene, with suggestions hidden. Its actual behavior is not yet labeled.
- Three guided scenes covering a candidate onset, a low-motion part of a candidate, and a candidate ending or continuation. Low centroid motion does not establish quiet posture or lack of flailing.
- One randomly selected eligible unflagged control, with suggestions hidden.
- The separate BA060 onset-extension follow-up described above, also hidden.

There are no overlapping windows within a new source. Targeted clip selection can expose failures efficiently but cannot estimate broad accuracy. The fresh runs remain **UNREVIEWED** until VAF returns scores. Blank, unsure or unseen footage must never become a negative label, and flailing remains unassessed. Later evaluation must retain the hidden/guided/control/follow-up distinctions.

## Evidence and checks

Local evidence root: `outputs/ba_turtling_boundary_image_20261007/`. Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_boundary_image_20261007`.

`BOUNDARY_COMPARISON.json`, `RESULT_SUMMARY.json`, `EARLIER_QUICK_REGRESSION.json` and `BOUNDARY_SENSITIVITY.json` retain the development comparisons. `IMAGE_MODEL_DIAGNOSTICS.json` contains the image experiment's folds and predictions. `FRESH_PLAN.json`, `CODE_SHA256.json`, `INPUT_VERIFICATION.json`, per-run results, `REVIEW_QUEUE.json` and `PACKAGING_RECEIPT.json` preserve selection, frozen inputs, scientific code and displayed scopes. Previous source hashes were checked; new TOML/session compatibility, trajectory coverage and source identities were revalidated on Firebird. Video metadata/stat checks refer to the earlier recorded source-video hashes; no claim of a new full-video rehash is made.

Thirty focused Python tests passed, including the 13 new boundary tests, and 28 scorer checks passed. The new scorer labels short hidden clips as scenes rather than complete runs. Encoding retains inclusive frame windows and exact counts; the media are embedded for portable offline review. Browser playback is not established by these software/media checks. Slurm analysis array 916948 completed all 20 cells. Serial encoding job 916970 was canceled to parallelize delivery; its first two completed clips were reused and its outputs preserved. Array 916973 completed the other seven clips, and dependent packaging job 916981 completed. No production promotion, broad BA release, social PSC change or dyadic turtling test was performed.

The downloaded scorer passed a second check of all nine embedded MP4 hashes,
decoded frame counts and 30 fps metadata. Both page scripts passed syntax checks;
hidden clips contain no prediction arrays, and the native overlay controls are
absent. First/middle/last images from the three guided clips were inspected for
visible arena footage. Both finished pages were copied to Downloads with matching
hashes. `DELIVERY_VERIFICATION.json` and `DOWNLOADS_DELIVERY.json` retain these
checks; they do not claim browser playback or biological approval.
