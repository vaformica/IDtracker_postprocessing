# BA turtling: quiet posture and upright circling

VAF's four returned review rounds exposed two failure modes: an overturned beetle can stop flailing without righting itself, and upright circling can trigger the movement-based detector. A separate **0.3.0-development** experiment substantially improves agreement with these scores. It is not a production release or independent validation. Original scores, the frozen 100-run predictions, the report collection, raw coordinates and production defaults remain unchanged.

The before-and-after viewer is `outputs/ba_turtling_refinement_20261007/review/START_HERE.html`, also delivered as `Downloads/BA_turtling_refinement_20261007/START_HERE.html`. It contains seven previously scored examples, about 3.1 minutes total, with VAF, original and revised timelines. It deliberately includes unresolved errors and a small regression. No additional scoring is required to inspect this comparison.

## What the returned scores establish

All **60 clips** have complete, attributed VAF decisions. The importer verifies the four scoring-set hashes, every clip ID and inclusive frame window, decision/state consistency, nonoverlapping intervals, frozen prediction hashes, and original coordinate-table hashes. Original exports are copied byte-for-byte into `original_scores/`.

The labels cover **68,453 displayed frames**, including the separate 1,429-frame prior-event follow-up. Only those displayed windows are labeled; a full BA run is not approved because one excerpt was accepted. All four full runs, four random controls and two QC scenes have explicit no-turtling labels. Two of the full runs had possible prior prediction exposure and remain separated from the two prediction-hidden runs. The 49 candidate excerpts are targeted, not a representative accuracy sample. The previous follow-up is also reported separately. Flailing remains unassessed.

The frozen detector had **1,972 missed frames (65.73 s)** and **1,125 extra frames (37.50 s)** in these clips. Three missed frames lack tracking coordinates despite VAF's positive visual labels. Those frames remain tracking-unknown; a missing coordinate is not evidence that the beetle righted itself.

## The experimental changes

`ba_turtling_continuity_experiment.py` consumes the existing recovery-gated mask. It does not change the initial death-feint gate or the prototype wake metric.

**Candidate onset needs more than a loop.** Each uninterrupted candidate segment must contain at least 120 observed frames. The experiment measures how much path remains after an 11-frame moving average and how often adjacent moving steps reverse by more than 90 degrees. A segment is retained when its smoothed/raw path ratio is at most 0.65, or at least 10% of qualifying turns are reversals. Qualifying adjacent steps are each at least one pixel. These are descriptive movement features, not a direct measurement of posture. Rejected short fragments and smooth loops remain explicitly **ambiguous and requiring review**, rather than being labeled upright. A short confirmed event is not rejected solely for being brief: the earlier Run 12 event remains detected.

**Quietness does not terminate an established hypothesis.** After a retained segment, the experiment continues the candidate while observed positions stay within 35 pixels of a fixed reference (the median of the segment's last 30 positions), with adjacent steps no larger than 20 pixels and recovery eligibility intact. Only another retained segment can renew that reference. This prevents an inferred tail from slowly moving its own reference across the arena. Missing coordinates, large jumps, loss of eligibility or spatial departure stop this extension. There is no backward extension and no interpolation. A quiet upright stop near the reference could still create an overly long tail; righting is not directly observed by this model.

The function receives no run IDs, human labels or frame-specific overrides. It runs on each full 7,200-frame window before excerpting the evaluation. Input coordinates are unchanged. The 101 full-window experimental prediction files include the separate historical follow-up; they are developmental sidecars, not replacements for the pilot's outputs.

## Results and limits

| Compared with VAF on displayed frames | Frozen detector | Experiment 0.3.0 |
| --- | ---: | ---: |
| Missed turtling, new 60-clip review | 65.73 s | 12.33 s |
| Extra turtling flags, new 60-clip review | 37.50 s | 1.90 s |
| Entirely rejected candidate scenes still flagged | 7 | 0 |
| Missed turtling, earlier 12 full runs | 8.43 s | 0.00 s |
| Extra flags, earlier 12 full runs | 3.67 s | 3.30 s |
| Errors in the earlier five-clip check | 0 | 0 |

New-review frame counts change from TP 26,966 / FP 1,125 / TN 38,390 / FN 1,972 to TP 28,568 / FP 57 / TN 39,458 / FN 370. These count the presence of a suggestion, not a validated upright-versus-overturned classifier: suppressed ambiguous loops are retained as review concerns. The 12-run comparison uses the corrected Run 1 onset of 2834 and the additional Run 12 interval 2908-3036. All seven older entirely negative runs remain unflagged. The prior five-clip check retains all 450 positive frames and 15,750 negative frames.

Specific remaining errors in the new review are:

- **BA069:** onset remains 217 frames late (7.23 s).
- **BA060:** the first 150 displayed frames are still missed (5.00 s). The clip begins while VAF labels the beetle on its back; the true onset before that boundary is not established here.
- **BA026:** 52 frames remain flagged beyond VAF's endpoint (1.73 s).
- **BA016:** the new continuation adds five extra endpoint frames (0.17 s).
- **BA069:** three isolated tracking-missing frames remain unknown (0.10 s).

In the older set, Run 2 gains three extra frames, while Run 12 loses 14 extra frames; no formerly detected positive frames are removed. Run 1's 253 missed frames are recovered. The initial death-feint exclusion is preserved.

**Threshold sensitivity matters.** An exploratory 3-by-3 check varied the smoothed-path cutoff (0.60/0.65/0.70) and reversal fraction (0.08/0.10/0.12). At 0.60 and 0.10, a true episode loses 1,500 reviewed positive frames; at 0.70 and 0.10, extra flags rise to 385 frames. This separation is promising but narrow. The scores and these checks informed the development settings, so neither the 60 clips nor the older regression sets now establish independent generalization. The six new-source clips from the earlier seven-clip validation were not re-evaluated in this task.

The next useful scientific check is a small independent set that includes upright circling, quiet overturned pauses, and actual righting followed by a nearby upright stop. Image appearance may be needed where centroid motion overlaps. More broad deployment should wait for that check; no dyadic turtling transfer or production promotion was performed.

## Evidence and verification

Local evidence root: `outputs/ba_turtling_refinement_20261007/`. Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_refinement_20261007`.

`SCORE_COMPARISON.json` preserves the frozen evaluation, subgroup counts, labels and per-clip mismatches. `REFINEMENT_COMPARISON.json`, `EARLIER_12_REGRESSION.json`, `EARLIER_QUICK_REGRESSION.json` and `PARAMETER_SENSITIVITY.json` record the tests above. `predictions/` retains per-frame candidate, ambiguous-loop and evidence states. `VIEWER_CLIPS.json` records exact plotted intervals.

Twelve focused software tests passed, covering circle ambiguity, quiet continuation, fixed-reference departure, tracking gaps, jumps, recovery eligibility, inclusive audit boundaries and immutable inputs. The comparison page's seven embedded videos match the previously scored bytes and have verified frame counts. Its script and frame/interval helpers pass checks. Browser playback was not tool-tested. These checks establish reproducibility and packaging, not biological validity.
