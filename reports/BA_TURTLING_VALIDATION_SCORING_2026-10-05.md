# Additional BA turtling scoring set, 5 October 2026

Vince offered to score further videos after development of the experimental onset/quiet-pause rules. The next set separates new-source evaluation from the remaining development pause check. It does not change the rules or existing labels.

## Selection fixed before scoring

Seed **20261005** randomly selects three source video paths not present in the initial three-recording scoring set, then one random eligible TOML per selected video. Eligibility uses the existing inventory: one animal, one ROI, one matching session, complete 7,200-frame coverage, no recorded settings differences or inventory flags. Current tracking must have at least 95% finite positions. Any post-selection failure is retained in the blocked list rather than silently replaced.

Selected new sources:
- Camera_2_40359705_20260627_1326_ACT1_D2
- Camera_3_40629046_20260627_1635_ACT2_A3
- Camera_3_40629046_20260628_1605_ACT2_A2

For each, the 0.1.0-experimental rule is frozen and run on the full 7,200-frame window. Two 16-second clips are selected: one around the first new experimental addition, otherwise the longest candidate onset, otherwise a compact-movement control; and one random non-overlapping window. A separate 12-second passage around the unreviewed 7251-7268 pause comes from the earlier Camera 2 C3 development recording. All seven clips are shuffled; source identity, selection role and predictions are omitted from the scorer. Total footage is 108 seconds.

The six new-source clips may support an initial evaluation of frozen rules on unseen recordings. Selection is enriched, not a random population sample; do not estimate population prevalence from it. The development pause clip is excluded from held-out metrics. If rules are tuned using the new labels, those examples become development data and another independent test set is needed.

## Scoring and delivery

The standalone HTML embeds every MP4, with native playback controls and frame stepping. Reviewer name is required for export. Posture and active flailing are recorded separately as never, throughout, only during specified inclusive global-frame intervals, or uncertain. Global frame start/end marking avoids ambiguous seconds-to-frame conversion. Quiet time on the back belongs to turtled posture. Browser storage is optional; JSON download/import provides portable progress and final labels.

The original source TOMLs, tracking and videos are read only. Source TOML/session/trajectory hashes, original baseline code hash, frozen experimental code, clip bounds, crop geometry, selection roles and MP4 hashes are stored in the analyst key. Each crop retains the source orientation and uses verified 30-fps input seeking and residual-frame trimming. Encoded frame counts must be 480 (new-source clips) or 360 (development clip).

Local root: `outputs/ba_turtling_validation_scoring_20261005/`.
Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_validation_scoring_20261005`.
Compute job: **916524**; consult live `VERIFICATION.json` for completion rather than inferring it from submission.
Durable review folder: `/Users/New/Downloads/BA_turtling_validation_scoring_20261005/`.

All behavioral labels remain **UNREVIEWED** until returned by Vince. The reviewer delivery contains only the standalone scoring page and instructions, not the analyst key or predictions. Scorer tests check frame marking, per-clip persistence, interval bounds, uncertainty, completion counts and exported intervals.

## Completion and verification

All seven clips are complete, with zero blocked selected sources. Job 916524 encoded and frame-count-verified the clips but failed while serializing NumPy crop coordinates in the analyst key. Job **916525** converted those metadata values to native integers, reused the existing videos unchanged, and reverified every encoded frame count. Both scripts and logs are retained. The build-stage receipt included an active retry log; the final receipt excludes changing scheduler logs and is the authoritative packaged-file hash list.

The delivered standalone HTML contains 108 seconds of verified H.264 video (six 480-frame clips and one 360-frame clip). All seven embedded video hashes match the analyst key. Scorer behavior tests pass, including exact global-frame intervals and complete/uncertain states. Safari displayed a tab with the correct page title, but active user navigation prevented a playback check; do not claim successful playback from this attempt.

The scorer and reviewer instructions are in the Downloads folder above. Predictions, source names and the analyst key are not included in that reviewer delivery. Rule parameters remain frozen pending scores.
