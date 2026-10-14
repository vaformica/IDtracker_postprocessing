# BA visual pattern review — October 12, 2026

AI-written synthesis by Codex. Automatic flags and image-screening results are review hypotheses. No scientific trajectories, detector rules, source TOMLs or IDtracker runs were changed.

The prior flag dashboard did not give Vince enough visual evidence to judge problems. The replacement is one portable HTML file with 10 short examples (4.0 minutes), paired low-resolution full-camera/cell videos, optional raw-position rings, full-window and excerpt trace images, and recording-wide brightness/missingness/jump plots. Video controls sit below the images. Decisions are request marked exclusions, approve shown tracking, flag problem, or unsure/need more footage. Notes and suspected causes are optional; scores can be downloaded at any stage and restored from JSON.

## Patterns already supported by the records

Across the existing 121 windows from 14 source recordings, 231 of 256 adjacent-frame jumps over 100 pixels occur in two recordings (90.2%). This is a concentration of a predefined tracking flag, not a measured error rate. In Camera_1_40169154_20260627_1614_ACT2, all nine analyzed cells jump within frames 1080–1109. In Camera_2_40359705_20260627_1326_ACT1, ten of eleven jump within 1020–1049. Coincidence across cells points toward a shared disturbance but does not prove its cause.

The full-image screen sampled all 14 source recordings every 15 frames. Around the first recording's initial disturbance, median grayscale brightness increases by 12 levels and nine of twelve image tiles brighten by more than eight levels between frames 1095 and 1110. Coarse phase correlation finds zero whole-pixel translation at 320×180 resolution in that pair. This supports a shared brightness event, but cannot distinguish a switched light, shadows, exposure adjustment, or smaller camera movement. At the second recording's transition, brightness is spatially mixed; it is a separate visual check, not automatically the same cause.

The first recording dims again around frames 1750–2135, coinciding with further jumps. The reviewer therefore contains two excerpts from it. A restart immediately after the first event may leave a later disturbance inside the analyzed window. Several unrelated missing-position cases and two no-threshold-flag comparisons are also included. These examples are purposive development/diagnostic selections, not a random accuracy evaluation. The initial lighting comparison was selected from the first four completed scans; later scans were retained for broader investigation rather than silently changing the review set.

## What the human TOMLs did exclude

Vince asked whether the human-created TOMLs already remove the setup period. They can, and the first example supports that: the person seen in the context image at frame 1050 is absent in the exact tracking-start image at frame 1095. No person is visible in the later frame-1950 snapshot either. The visible setup before the TOML start is not evidence that the TOML was wrong. Lighting/shadows or other disturbances may still occur afterward, including from outside the camera view.

A follow-up exact-frame audit confirms brightness fluctuations after some starts: first example starts at 1095 with changes at 1098, 1099, 1102 and 1109; the rotated recording starts at 822 with a jump at 824; another starts at 980 with changes at 980–981. The second shared-jump recording starts at 760 and has a later large brightness change at 1022. These are image measurements, not proof of a physical switch being operated. Results are preserved in START_BOUNDARY_AUDIT.json.

Some review excerpts deliberately begin before the TOML start. The viewer labels those frames as context only, draws the selected start on the recording plot, and exports both displayed coverage and its intersection with the analyzed window. It does not count pre-start footage as missing tracking. Optional 'Setup correctly excluded by TOML' observations allow this distinction to be recorded.

## Exclude only confirmed bad frames

Vince's final instruction supersedes the earlier restart proposal: remove only specifically identified disturbed frames from IDtracker, retaining usable footage before and after. The reviewer marks first and last bad frames (both inclusive), supports several separate gaps, and records whether they apply to one cell or the same recording. No real exclusions or tracking jobs have been submitted; exact ranges await attributed review.

The installed IDtracker supports multiple half-open tracking intervals, confirmed using its processing-episode planner. Its environment is named idtrackerai_6_0_14, but the installed package reports 6.0.10. This was a capability check, not a tracking run. The new standalone ba_tracking_exclusions.py prepares a derived TOML and provenance receipt from explicit review requests; it preserves the source and all other settings. Tests verify exact frame-set subtraction and scope safeguards.

Keep the original 7,200-frame temporal window and global frame numbers. Exclusions reduce eligible observations; never replace them with later footage or treat them as negative behavior. No motion or posture continuity may be inferred across excluded gaps. The existing production BA processor still requires one interval, so pause-aware postprocessing must be implemented and tested before a rerun can become an analysis release. Excluding transient frames also does not guarantee that segmentation works under the changed lighting afterward.

## How to use the returned decisions

Exports use `ba-visual-pattern-review-v2`, bound to the exact CASES.json hash. Approvals cover shown tracking in the selected cell/window only. Cause tags are qualitative observations, not frame-level posture annotations, exclusions, or approval of every cell in a recording. Blank and unsure examples remain unreviewed/unknown. The prior turtling scores, current manual-flag dashboard and frozen detector remain unchanged.

After Vince's review, group accepted causes by source video and frame range; compare affected sibling cells, missingness and jump timing; separate repeatable recording-wide effects from isolated failures. Test reviewed frame exclusions on a few affected cells and compare to preserved originals before extending it broadly. Known BA060 onset failure remains a separate turtling limitation.

## Examples

| Case | Run | Original global frames | Purpose |
|---|---|---|---|
| case_01 | fresh_04 | 648–1547 | Shared early disturbance |
| case_10 | fresh_04 | 1600–2499 | Later disturbance in the same recording |
| case_02 | ba_006 | 585–1484 | A second shared disturbance |
| case_03 | fresh_17 | 375–1274 | Possible recording-wide lighting change |
| case_04 | ba_004 | 4850–5449 | Repeated loss of the beetle |
| case_05 | ba_069 | 1180–1779 | A smaller tracking gap |
| case_06 | ba_015 | 900–1499 | Circling or overturned posture? |
| case_07 | ba_060 | 3642–4241 | Known missed turtling onset |
| case_08 | ba_001 | 4250–4849 | Comparison: no threshold flags |
| case_09 | ba_002 | 3960–4559 | Comparison: no threshold flags |

## Verification and evidence

Encoded MP4 frame counts and 30 fps metadata are checked for every cell and full-context clip. Extraction uses a whole-second seek followed by exact frame trimming. Selected TOML hashes are checked against the census, coordinate-input hashes are recorded, and raw video sizes/mtimes are retained (full videos were not rehashed here). Trace plots preserve missing gaps and distinguish >100 px jumps. Synthetic checks of the actual image-screening function separate unchanged images, known translation and uniform brightening; this is not biological validation. The actual reviewer script is checked for paired seeking/frame stepping, decision scope, saving, exports and mismatched-import rejection. Representative trace plots and source images are visually inspected. Browser playback itself has not been directly tool-tested.

Local evidence: outputs/ba_visual_patterns_20261012. Firebird: /data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_visual_patterns_20261012. Portable user copy: /Users/New/Downloads/BA_visual_patterns_20261012/START_HERE.html. The review's videos and images are embedded, so it needs no local server or loose media files. No new IDtracker batch was submitted. The scan and media-building jobs are derivation jobs only; failed/intermediate attempts are preserved.

## Frame-step control fix

After VAF reported that +1 frame did not advance, the viewer now maintains an
explicit paused frame index and seeks to the midpoint of the requested frame.
This avoids depending on stale/rounded currentTime during browser seeks. Forward,
backward, repeated-click and clip-boundary tests pass against the actual script
with simulated stale video time. Native browser playback remains unverified.
The case hash, localStorage key, JSON schema, and scored scope are unchanged;
Downloads and Firebird copies were updated. Reload the page to use the fix.
