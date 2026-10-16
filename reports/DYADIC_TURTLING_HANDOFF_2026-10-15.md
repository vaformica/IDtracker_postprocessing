# Dyadic turtling handoff — October 15, 2026

**Later update:** QC integration and the 25-run local dashboard are now implemented. Read [the QC integration record](DYADIC_TURTLING_QC_2026-10-15.md). The following checkpoint describes the state before that integration.

Vince requested saving the current turtling work for use from another chat. The next authorized task is to add possible-turtling QC to the existing 25-run dyadic dashboard, with video links and raw movement traces. That integration has NOT been implemented. No full batch, production behavior change, or six-beetle work was started.

## Script to call

`dyadic_turtling_experiment.py`, version `0.1.0-development`, is a standard-library-only candidate screen:

```python
from dyadic_turtling_experiment import screen
# raw[frame][identity][xy], exactly two IDs, original-image pixel coordinates.
# Pass the raw IDtracker array, never inferred PSC positions.
result = screen(raw, target_id=0)
# Repeat for target_id=1. Frame indices are relative to raw's first row.
# Add the source window start to obtain global video frame numbers.
```

It returns `quiet`, `loop`, `context`, and `states`. Defaults use 120-frame windows and assume 30 fps. Quiet support requires complete tracking, radius90 <=3 px and maximum adjacent step <=5 px. Loop support is a localized tortuous-motion heuristic. See the source for all frozen thresholds. It is not a validated anatomical posture classifier and has no standalone command-line interface.

Preserve `INTERACTION_AMBIGUOUS` candidates in the future dashboard: nearby or unobserved partners do not rule out turtling. `TRACKING_UNKNOWN` is unknown, and `NO_CANDIDATE_NOT_A_POSTURE_LABEL` is not an upright label. Neither candidate durations nor immobility durations are confirmed turtling duration. Any non-30-fps integration requires explicit time-window handling and tests; do not silently reuse frame thresholds as seconds.

`dyadic_posture_image_experiment.py`, version `0.1.0-image-development`, is the separate crop-feature/logistic-regression feasibility experiment (NumPy/Pillow required). It is saved for reproducibility, not recommended for automatic production labels. Its fitted predictions and model records remain in ignored `outputs/dyadic_posture_images_20261015/native/`; they are not embedded in the source module or Git commit. Historical training labels have identity ambiguity and require audit before refitting.

## Latest human evidence

VAF's clarification confirms ID 0 on back and ID 1 not turtling at:

- Camera_2_40359705_20260701_1650_FIGHT_ACT2_A1: 7032–7179 inclusive.
- Camera_1_40169154_20260702_1535_FIGHT_ACT2_A2: 2720–3169 inclusive.
- Camera_1_40169154_20260630_1633_FIGHT_ACT2_PAPER_DATA_WRONG_C2: 5146–5595 inclusive.

Clip 1's other 302 displayed frames are unmarked in this clarification. Earlier scene-level positives must not automatically be assigned to a target ID. The frozen image model still incorrectly flags ID 1 in 27/28 sampled images from the third clarified clip. Read `DYADIC_POSTURE_CLARIFICATION_RESULTS_2026-10-15.md`. Original scores and attributed intervals are preserved under `outputs/dyadic_posture_clarification_results_20261015/`; local review is on port 8796. These artifacts remain outside Git.

## Resume QC integration

Use `outputs/psc_review_qc_20261005/QC_RUN_INDEX.json`, filter `collection == 'dyadic'` (25 runs). Each corresponding `runs/<run>/` has `analysis/canonical_states.npz` (raw array), `review/source_manifest.json` (fps, video, geometry), `QC_SUMMARY.json`, `QC_EVENTS.json`, and an existing review with global-frame deep links. Preserve frozen artifacts and create a new versioned output directory. Source identifiers include the video and TOML cell.

`unified_qc.py` currently handles general recording/tracking QC; `run_six_beetle_pipeline.py` calls it for the shared group route. Integrate only the requested dyadic candidate sidecars, explicitly retaining posture as unconfirmed. Add target identity, inclusive global-frame interval, quiet/loop support, partner context, missing tracking, and direct video access alongside traces. Add human choices per beetle, not an ambiguous scene-only target label. Include unflagged review controls to assess misses. Do not infer “alone” from missing partner coordinates. Keep PSC and scientific movement outputs unchanged.

Current six-beetle development remains on hold. Production PSC is 1.6.0 / group processor 0.8.2-group. None of the turtling experiments supersedes those engines or the separate BA posture work.
