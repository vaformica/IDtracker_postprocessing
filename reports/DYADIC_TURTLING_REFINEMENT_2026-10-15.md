# Dyadic turtling refinement — October 15, 2026

Vince's first seven-clip review confirmed three full on-back excerpts and 532 on-back frames in a nearly motionless beetle. He also identified fighting that resembled the old looping criterion. This experiment uses those observations to improve review selection; it does not establish automated posture durations.

## What changed

`dyadic_turtling_experiment.py` version **0.1.0-development** is separate from production. It uses full-precision raw IDtracker coordinates from the existing CSVs, never PSC-estimated locations. The previous loop rule is retained alongside a new quiet-position screen: a complete 120-frame window (4 seconds at 30 fps), 90th-percentile radius at most 3 original-image pixels, and no adjacent step above 5 pixels. Passing windows mark their observed frames as quiet review candidates. Quiet upright rest can pass this screen; this is the main question for the new controls.

When a candidate coincides with a partner within 60 pixels, or the partner's position is unavailable, its state is **INTERACTION_AMBIGUOUS**. Missing target positions remain **TRACKING_UNKNOWN**. Neither state is a negative posture label. The old loop and new quiet masks remain available beneath these states, so ambiguity does not erase evidence. No fungus veto is used in this experiment; on-fungus candidates remain reviewable. This can reveal false positives previously hidden by that veto.

These rules use position geometry to prioritize video inspection. They do not distinguish backs from upright beetles, establish identity through piles, or measure flailing. They are intentionally not wired into `six_beetle_processor.py`, PSC, BA, or batch metrics. Six-beetle work remains on hold.

## Comparison with Vince's scores

The original export remains unchanged. Seven identities, frame ranges, and source hashes were checked on import. Only explicit marked intervals supply frame labels; overall negative assessments do not become hundreds of negative frames.

| First review clip | Result under revised screen |
| --- | --- |
| 1, on back throughout | 550 loop candidate frames; 50 interaction-ambiguous frames, all still retained as underlying candidates |
| 2, on back throughout | 600 loop candidate frames |
| 3, fighting note | 594 interaction-ambiguous frames and 6 target-tracking-unknown frames; no individual posture assignment |
| 4, on back throughout | 405 loop candidate frames; **195 positive frames still missed** |
| 5, quiet beetle | All **532 marked positive frames** now quiet candidates; old loop screen flagged none |
| 6, overall negative | 131 loop candidates on fungus; remains a potential false-positive example, without frame-level negative labels |
| 7, overall negative | No candidates; 215 target-tracking-unknown frames remain unknown |

Across the 2,332 explicit positive frames, 2,087 receive individual review-candidate states, 50 receive interaction ambiguity, and 195 have no candidate. This is a development fit, not an independent accuracy estimate. Clip 5's 68 unmarked remaining frames are not assumed upright; the new screen flags those too and the continuation review tests that uncertainty. Clip 3 has no explicit negative intervals, so no frame-level specificity or false-positive rate is calculated.

## Next review

`outputs/dyadic_turtling_refinement_20261015/START_HERE.html` is a separate round with separate browser storage and export name `Dyadic_posture_round2_scores_20261015.json`. The original reviewer and exported scores remain intact. Six excerpts each contain 600 frames at 30 fps: **two minutes total**.

Two are development follow-ups: continuation around the quiet beetle's previously unscored endpoint and the fighting excerpt for explicit negative/uncertain interval scoring. Four are from runs not in the first posture set: two quiet-candidate examples, an interaction-ambiguous example, and an unflagged control. Selection favors different recordings when available but comes from the existing cached collection; it is targeted, not a random sample or an independent-recording validation. No qualifying new-run loop excerpt met the 300/600-frame selection requirement, so a second quiet candidate was used instead. Exact selections, source hashes, code hash and parameters are in `MANIFEST.json`.

Predictions and reasons are not shown on the scoring page. This is prediction-hidden review, not strictly blinded: the two follow-ups are familiar and the selection rationale is known. Mark explicit **On back**, **Not turtling**, **Uncertain**, or **Not visible** intervals. Full-clip viewed means coverage, not a posture label. Radio buttons are retained throughout.

Next decision: inspect whether quiet flags mostly represent overturned posture or ordinary rest, and whether interaction ambiguity preserves true overturned animals without misreporting fights. Refine visual evidence or boundary support before promoting any rule. Do not fit away remaining errors by extending to the known human endpoints.

## Verification

Eight synthetic tests pass (quiet candidates, proximity boundary, missing positions, jumps, motion, loop distinction and shape validation). The standalone loop calculation agrees exactly with the existing NumPy implementation on all seven original 600-frame excerpts; this is software parity, not biological validation. All six new videos independently decode to 600 frames. Browser playback, one-frame advancement, radio selection, offset labels and inclusive interval entry were checked. The temporary test interval was removed. `VERIFICATION.json` stores hashes and checks; `PREVIEW.png` records the interface.
