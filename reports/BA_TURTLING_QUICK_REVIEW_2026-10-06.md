# A short BA review before wider processing

**7 October update:** All five scores have been returned and match the frozen predictions over the displayed frames. See [the scored results and limits](BA_TURTLING_QUICK_REVIEW_RESULTS_2026-10-07.md). The preparation and delivery record below is retained as history.

Vince agreed to another small round of checks before applying the turtling detector broadly. This review freezes the current development rules and gives him five videos in one portable scorer: two complete runs with predictions hidden, followed by three 20-second scenes. The total video time is nine minutes at normal speed. Only posture needs scoring; flailing is explicitly unassessed.

The full runs help reveal events the detector missed. The short scenes include one suggested event and two randomly selected unflagged windows. A short-scene decision applies only to its displayed frames. It cannot approve an entire run or establish the total duration of an episode that extends beyond the clip.

## Selection and limits

The eligible pool contained 175 unused runs from 14 source recordings, after excluding previously used cells and incompatible, ambiguous, or unmatched records. Seed 202610062 selected one run per recording. Two were assigned to full-run review before computing predictions. The first is from the only entirely unseen eligible recording; the other is a new cell from a previously reviewed recording. Therefore, this collection is not wholly independent at the recording level.

Thirteen of the 14 selected runs could be analyzed. The selected B2 cell in `Camera_2_Straw_40359705_20260716_1514_EPOCH_BA` failed the completeness gate of at least 95% finite positions over the 7,200-frame window. Its blocked record was retained without silent substitution. Among the remaining short-scene pool, the detector proposed just one episode. The planned maximum of six candidate scenes consequently became one; the two preselected full runs and two random unflagged scenes remain. This is a reduced development check, not an accuracy estimate for the whole BA collection.

The previously documented camera-artifact frames 1098 and 1099 were supplied to the recovery gate only for the same source recording. No posture labels were transferred into these new runs. Camera-motion detection remains a known limitation.

## What is frozen

The predictions combine `ba_turtling_episode_experiment.py` 0.2.0-development with `ba_turtling_recovery_gate.py` 0.1.0-development, using the original prototype candidate seeds. Both remain outside the production defaults. The prior Run 12 correction is already preserved separately in [the human-score correction record](BA_TURTLING_RUN12_CORRECTION_2026-10-06.md).

`selection_key.json` ties each clip to its TOML, immutable IDtracker trajectory, source recording, global frame window, crop, predictions, sampling role, and code hashes. `SOURCE_VIDEO_HASHES.json` records the five displayed source-video hashes and a recheck of TOML/session/trajectory hashes. The public scorer omits predictions for the first two full runs and omits analyst selection roles.

## Scoring and evidence

The scorer uses inclusive original global frames, controls below the video, one-frame stepping, a numeric frame jump, and optional boundary adjustments. Decisions are accept, no turtling, adjusted intervals, or unsure. Explicit negative answers are distinct from blank clips. An open start remains unfinished. The last clip saves without requiring Next. Scores can be downloaded at any time and reimported into the same scoring set; browser storage is a convenience rather than the sole copy.

The exported schema is `ba-guided-turtling-review-v1`. It records reviewer initials, scoring-set fingerprint, per-clip completeness, inclusive posture bounds, notes, revision history, and `flailing_status: not_assessed`. Unsure exports a null posture label, not a negative label. Consumers must honor both the completeness flag and the displayed-only review scope.

Local evidence root: `outputs/ba_turtling_streamlined_review_20261006/`.
Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_streamlined_review_20261006`.
The delivery file is `review/START_HERE.html`, with embedded H.264 video. `PACKAGING_RECEIPT.json`, `SCORER_TESTS.txt`, and the final delivery verification record distinguish media/software checks from human review. Browser playback is not asserted by the software tests.

No new IDtracker runs or all-BA batch were launched. After Vince returns this score file, compare the frozen predictions against his labels over exactly the reviewed frames. If a rule changes, keep this scored set as development evidence and seek a further independent check before broad deployment.

## Delivery checks

Preparation job 916657, all five video tasks in array 916658, and source-verification job 916663 completed successfully. All five H.264 files passed exact encoded frame counts, 30-fps timing, expected crop dimensions, and hash checks after retrieval. There are 16,200 frames in total. Beginning, middle, and end samples were visually inspected for all five crops. Twenty-two scorer checks passed, including frame stepping, inclusive boundaries, explicit negatives, unfinished marks, last-clip saving, and score import/export. The packaged script compiled and all five embedded media hashes matched the checked MP4s. These checks do not assert browser playback or biological validity.

The 44.3 MB standalone file was copied and read back at `/Users/New/Downloads/BA_quick_turtling_review_20261006/START_HERE.html`. Its SHA-256 is `71b2d7762089b722b42d738b66d8cc882853595eea62e13eb626f936f85a1616`. It contains no required external media or server dependency. The same file is retained on Firebird under `review/START_HERE.html`. No human decisions have yet been returned for this set.
