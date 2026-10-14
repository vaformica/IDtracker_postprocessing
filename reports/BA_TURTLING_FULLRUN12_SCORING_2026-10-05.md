# Twelve complete BA runs for turtling scoring

**Scoring returned, 6 October:** all twelve runs now have attributed annotations, including Vince's direct confirmation that seven blank entries were negatives. The [completed comparison](BA_TURTLING_FULLRUN12_RESULTS_2026-10-06.md) finds close agreement in the random subset but a substantial missed-duration problem in targeted Run 1. The detector remains experimental; the sections below retain the preparation and interface history.

Vince requested another 10–12 videos after the seven-clip comparison matched the experimental posture candidates. This round examines complete four-minute windows so false alarms, missed episodes and recovery boundaries outside short excerpts can be scored. Posture and active flailing remain separate human annotations. Automatic rules are unchanged, and no new human labels have yet been collected.

The set contains **12 different runs from eight previously unscored source recordings**, each covering 7,200 inclusive frames from its TOML tracking start at 30 fps: **48 minutes in total**. The six source recordings used in earlier development and scoring are excluded. Eight runs are selected randomly, one per new eligible recording, before inspecting predictions. Four additional runs use different cells from four of those recordings and are selected to challenge the detector. These extra runs share recording conditions with the random subset and must not be counted as four additional independent source recordings.

Selection uses seed **2026100512** and an archived inventory. Ninety-nine inventory entries meet the structural/session requirements; current screening retains 97 with matching TOML/session hashes, one animal and one arena, full window coverage, at least 95% finite positions, and 30-fps video. Both screening failures remain recorded. These are sampling requirements, not instructions to exclude those runs from the research dataset.

The four challenge rankings, in order, are the most newly added experimental frames, the longest candidate bout with both boundaries inside the analysis window, the most stationary non-candidate frames, and the most candidate bouts. Each chooses an unselected run from a different source than the other challenge runs. These movement patterns suggest useful tests but do not establish flailing, grooming, rest, inversion or recovery. The reviewer pages hide both the selection category and predictions.

The frozen baseline comes from the existing pilot code snapshot and is checked against the baseline hash recorded for the previous validation set. The experimental code is the same **0.1.0-experimental** snapshot. Full-window predictions are preserved before human scoring. Future evaluation must report the eight random runs separately from the four targeted challenges, include onset/recovery and duration errors, and retain uncertainty. If these labels inform rule changes, they become development data rather than an independent test of the revised rules.

For convenient offline review, three standalone pages each embed four complete videos. Each part has its own browser-storage key, score-file name and public-clip checksum. The repaired Save and Download controls are retained; the final run can be scored negative and exported without further navigation. The pages display run numbers 1–12, support frame stepping and inclusive interval marking, and offer normal, slower, 2× and 4× playback. Faster playback is a convenience, not a substitute for inspecting ambiguous transitions. The reviewer returns **three JSON files**.

Local evidence root: `outputs/ba_turtling_fullrun12_scoring_20261005/`.
Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_fullrun12_scoring_20261005`.
Reviewer folder: `/Users/New/Downloads/BA_turtling_fullrun12_scoring_20261005/`.

Build job 916527 completed screening and fixed selection; its sequential encoding was stopped to shorten the wait. Its partial files remain under `attempt1_sequential/` with its original log. Array job **916529** encodes the same shuffled selection concurrently. Consult the final verification receipts for completion; job submission alone does not prove delivery or playback.

## Completed build and checks

All twelve array tasks completed; package job **916537** and visual-check job **916542** completed. Every H.264 video has exactly 7,200 encoded frames at 30 fps and a 240-second duration. Source TOML, session and trajectory hashes, and both frozen detector hashes, were checked. All 131 files in the initial final package receipt matched after download; later presentation-only wording changes and local test receipts are covered by the refreshed receipt. The original source videos also have recorded SHA-256 hashes.

All twelve embedded video copies match their checked MP4s. Programmatic tests pass on each actual scoring page, including correct run IDs, four complete windows per part, separate export names, saving a negative final run without navigation, and an inclusive one-frame interval at the last frame. Decoded start, midpoint and final-frame previews were visually inspected for all twelve runs: the arena crops and beetles are visible. This checks presentation, not the behavioral classifications.

The delivered parts are about 109, 110 and 116 MB. Source filenames and predictions are hidden; physical labels already printed in the source footage remain visible, so this is not complete blinding to recording identity. The browser tool's security policy blocked local-file URLs. No alternate-browser or server workaround was attempted, and native browser playback is **not verified** in this turn. The files use the established offline embedded-video format, and the user should open `START_HERE.html` in Safari or Firefox.

Status: **READY_FOR_HUMAN_SCORING_UNREVIEWED**. These are scoring materials and frozen hypotheses, not a validated detector release. The three JSON exports must be retained with their part IDs and checksums when Vince returns them.

## Easier interval scoring, 6 October 2026

At Vince's request, scorer **0.3.0** adds Start both (on back and flailing), separate Start and Stop buttons for each behavior, and Continues to end. Stop automatically saves an inclusive interval through the current frame; repeated bouts require another Start/Stop pair. Posture can remain active while flailing stops. Cancel start removes only an unfinished start. Editable intervals and the Never, Throughout and Uncertain choices remain available.

Unfinished starts survive navigation, reload, partial export and import, but prevent a run being marked complete until stopped, extended explicitly to the end, or cancelled. The scorer uses a separate version-3 browser storage key and can load prior version-2 progress without overwriting it. Part IDs and public-clip checksums remain unchanged, so earlier JSON exports remain compatible. The same twelve embedded videos and frozen predictions are retained.

The original scorer evidence remains in its existing Firebird root. The successor is `outputs/ba_turtling_fullrun12_buttons_v030_20261005/` locally and `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_fullrun12_buttons_v030_20261005` remotely; its date suffix identifies the original scoring cohort. Updated reviewer files replace the same five filenames in the Downloads folder, with the previous files retained in `Previous_version_0_2_0/`. Close old scoring tabs and reopen the updated files. No human score exports are changed.

Tests cover combined and independent starts, independent stops, repeated bouts, inclusive endpoints, backwards-seek rejection, ending at the final frame, cancellation, pending-start persistence and export/import, and migration of older scores. The actual three rebuilt pages also undergo export and embedded-media checks. These software checks do not constitute native-browser playback verification.

## Unobstructed video controls, 6 October 2026

Vince's screenshot showed the native playback overlay obscuring the arena's lower edge. Scorer **0.3.1** removes native video controls and places a frame-based seek bar plus Play/Pause, frame stepping and speed controls in a separate block below the video. The Start/Stop buttons remain below those controls. Scoring IDs, storage keys, imported scores, pending starts and video bytes are unchanged.

The page now explains why flailing is separate: the target measure is all time on the back, including quiet intervals. Flailing is a secondary validation label used to assess whether movement-based candidates miss quiet turtling; it does not define or limit turtled duration. No detector thresholds or annotation meanings changed.

Successor evidence root: `outputs/ba_turtling_fullrun12_player_v031_20261006/`, mirrored under the same name in Firebird's `idtracker_pipeline_runs/`. The same Downloads files are updated, with the prior 0.3.0 pages retained under `Previous_version_0_3_0/`. Tests additionally verify native controls are disabled, the seek control is structurally below the video, seeking reaches the first and last global frames, and seeking does not alter behavior annotations. Native-browser rendering remains unverified by the tools; the supplied screenshot established the original overlap.
