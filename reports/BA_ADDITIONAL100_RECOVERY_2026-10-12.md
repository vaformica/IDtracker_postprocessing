# 100 additional BA cells: correction and QC review

AI-written by Codex, 12 October 2026. **COMPLETE_UNREVIEWED. All 100 cells delivered; awaiting human review.**

VAF authorized 100 additional cells after reviewing the frozen transfer test.
The purpose is to recover major tracking errors while keeping the original
tracking available, and to make the remaining problems easy to inspect.

The census identified exactly 100 cells with compatible existing tracking but
no confirmed previous BA analysis record, across 14 recordings. These are not
100 new recordings or an independent population sample. Each uses 7,200 inclusive
frames from its source TOML start. Exact settings and readable archived tracking
were checked live. Two stale registry paths were replaced by compatible archived
sessions before processing. Session selection prefers the archive, then the
lexicographically first exact-settings compatible session; it does not select
whichever trajectory gives the most favorable QC result. Alternatives are recorded.

Original videos, source TOMLs and IDtracker coordinates are immutable inputs.
Each output retains a raw array, a separate proposed array and input hashes.
No new IDtracker jobs or changes to production behavior measures are included.
Candidate recovery and the major-jump, excursion and stationary correction modules
are byte-identical to the frozen transfer snapshot. The 18 focused rule tests pass.
The same short-window stationary eligibility policy is retained. Starting-window
repairs remain a special review concern following the BA059 rejection and BA082
trace flag in the latest human feedback.

The viewer has original/proposed panels, traces visible by default, global frame
controls below the video, separate trace/video decisions, and downloadable scores.
Problem scenes cover changes, raw major jumps, missing tracking and possible
brightness disturbances. Long problem stretches are split into scenes of at most
300 frames. An unchanged-region spot check is included where available. Every run
also has a full 7,200-frame comparison for context beyond the short scenes.

## Review order

The index sorts by transparent QC tiers, with optional sorting by original jumps,
remaining jumps, missing percentage or changed positions:

- Highest priority: remaining steps over 100 pixels, at least 10% missing tracking,
  any newly proposed missing observations, or changes within the first 60 frames.
- Next: other proposed corrections, missing tracking or brightness candidates.
- Lowest: no measured flags; spot-check tracking.

Within each tier, remaining jumps, proposed missing percentage, added missing,
replacements and original jumps determine order. These are practical review
priorities, not calibrated probabilities of an error. Brightness candidates use
adjacent changes in median arena brightness; they do not establish a lighting
or shadow cause and can miss local shadows or camera shifts. This batch does not
recalculate turtling confidence. A plausible trace does not establish correct
beetle location, and automatic proposals do not become approved by passing tests.

## Files and execution

Local working root: `outputs/ba_additional100_recovery_20261012/`.
Firebird: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_additional100_recovery_20261012`.
Analysis/review array: **918599**; dependent ranked index: **918616**.

`PLAN.json` records all source and session choices. `PREFLIGHT.json` records live
input checks. Per-cell `POLICY.json`, `FINAL.npz`, `FINAL_AUDIT.json` and
`REVIEW_SUMMARY.json` distinguish proposals from raw tracking. `HASHES.json` and
`DELIVERY.json` document per-cell completion. Batch `RELEASE_RECEIPT.json` is the
completion authority; incomplete cells must remain visible in the index.

No completion claim should be made from job submission alone. Final checks and
local viewer delivery remain pending while the array runs.

## Light-exclusion provenance correction during preparation

The census preceded the authorized two-frame light-exclusion reruns. Eleven
selected cells from `Camera_1_40169154_20260627_1614_ACT2.mp4` therefore initially
used older tracking. Those new recovery tasks were stopped and their entire
attempt folders preserved under `superseded_original_tracking_attempts/`.
Their replacements use the already-verified light-exclusion IDtracker sessions,
with no new IDtracker submission. Replacement recovery array: **918694**.
`PLAN_before_light_rerun_adoption.json` preserves the earlier choices.

The three correction modules and their thresholds remain frozen. A separate
candidate adapter resets forward/backward tracking state at excluded frames;
stationary evidence windows split at the gap. Tests check both directions and
window splitting. The viewer labels those observations as human-excluded and
missing percentages use 7,198 eligible observations, not 7,200. This explicit
adapter is new handling of the previously authorized gap, not new biological
validation. The reruns' IDtracker exit-code warnings remain documented alongside
the independent output checks. Final validation job: **918650**, after the index.

## Completed review delivery

All 100 cells completed. The final baselines contain 723 adjacent-frame steps
over 100 pixels; the proposals contain 230. There are 1,046 replacement positions
across 26 cells; 74 full-run arrays are exactly unchanged. No additional missing
observations were proposed. The 22 previously authorized excluded observations
(two in each of eleven cells) remain explicitly excluded. These are QC counts,
not frame-level accuracy or biological approval. Initial census counts used
older tracking for eleven cells and must not be subtracted from final results
to estimate the correction algorithm's effect.

The 398 short scenes contain 50,461 encoded frames, or 28.03 minutes at 1x.
All 100 full-run views retain 7,200 frames each. Nine cells still have major
jumps; the highest-priority cell, new_015 (Camera1 1614 ACT2 A3), retains 192.
Codex also flagged new_041 frame 933 after a static image check: the proposed
marker appears below the beetle. That is an AI review concern, not a human label.

Delivery: `/Users/New/Downloads/BA_additional100_recovery_20261012/START_HERE.html`.
Use **Problems** for short scenes, **Full run** for context, and the order menu
for QC priority, original jumps, remaining jumps, missing percentage or changes.
Traces are visible by default. Export scores from each run's viewer.

Verification passed: 100 full MP4 frame counts, 398 clip frame counts, 1,194
clip-to-full-video alignment checks, and 42 original-video checks across all
14 recordings. All 1,896 downloaded hashed files matched their remote hashes.
The index sorting/filtering and all 200 scene/full-run pages passed frame-step,
synchronization-logic, final-scene saving and score-import guard checks. Six
static original/proposed image pairs and a representative trace plot were
visually inspected. Browser playback itself was not tool-tested.

`REVIEW_VALIDATION.json`, `RELEASE_RECEIPT.json`,
`LOCAL_DELIVERY_VALIDATION.json`, `VIEWER_LOGIC_VALIDATION.json` and
`FINAL_CODE_VERIFICATION.json` record these checks. Source science outputs
and turtling rules are unchanged; all proposed corrections await human decisions.
