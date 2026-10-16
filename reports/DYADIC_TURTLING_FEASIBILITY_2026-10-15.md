# Dyadic turtling: first troubleshooting set, October 15

Vince asked to investigate dyadic turtling using existing videos, including earlier processors with large candidate counts. No production rule was changed or tracking job submitted. This is candidate selection for attributed posture review, not a validated detector.

## Historical evidence found

Read-only retrieval of `/home/vformic1-swat/idtracker_reprocessing_v1/combined_results_latest.csv` found 597 rows. The search ranked 175 rows whose source video names explicitly contain Fight; this is not a reconciled inventory of all experimental fights. The historical table labels the processor 0.7.0 and records six cumulative turn rotations; current legacy code defaults to three. Other input and window differences must also be checked before comparing versions.

| Source recording / cell | ID | Historical candidate frames | Fraction of detected frames |
|---|---:|---:|---:|
| Camera 1, June 30 16:33 WRONG / C2 | 0 | 3648 | 0.5066 |
| Camera 2, June 30 16:34 WRONG / B3 | 1 | 2437 | 0.3435 |
| Camera 1, July 1 13:32 / B2 | 0 | 2236 | 0.3105 |

C2 and B2 are represented in the current clip set. B3 is retained in the historical follow-up ranking but its footage was not included in this first set. The historical 99-run PSC 1.5.1 package was withdrawn; retained metadata does not restore deleted scientific results. Earlier 0.7.0-group local smoke examples had zero turtling flags.

## What needs troubleshooting

The shared dyadic processor currently calls the legacy 120-frame tight-loop trajectory detector. Quiet overturned animals may fail its minimum movement/radius/turn requirements, while upright circling can pass. This is not a posture classifier. Current dyadic code also suppresses candidates inside fungus polygons, which can hide on-fungus events, and separately computes candidates from PSC-estimated paths. Inferred/borrowed positions cannot establish an individual's posture or flailing. BA boundary model 0.4 is not a proven replacement: human-reviewed BA060 had a large missed on-back episode despite finite coordinates. Do not blindly transfer BA's initial death-feint assumption to fights, where posture can change during interactions.

## Review set

`outputs/dyadic_turtling_feasibility_20261015/START_HERE.html` contains seven 600-frame excerpts (20 seconds each at the recorded 30 fps), four long-candidate examples, one quiet off-fungus control, one on-fungus control and one reported interaction/mount example. These are selected examples, not a random accuracy sample. The on-fungus control is the lowest-radius qualifying block available in the searched pool, but its 98.1-pixel radius is not quiet posture.

The search used the ten videos already cached in the comment review, after ranking full-window flags across 25 current dyads. Recomputed clip-selection masks use rounded viewer coordinates, so they are not exact reproductions of full-precision exported masks: C2 has 3677 exported candidate frames, 3654 from viewer-coordinate recomputation, and 3648 in the older 0.7.0 table. Those values must not be treated as a controlled model comparison. Exact inputs and hashes are recorded in SELECTION_AUDIT.json. The original review footage was reused; no source images or scientific tables were edited.

Each clip's target is a raw IDtracker identity, with optional offset annotation. Uncertain identity, occlusion or insufficient resolution must remain uncertain. Mid-clip screenshots were inspected for available content; no posture labels were inferred from those images. Future posture scoring should use higher-resolution source crops if these review encodes cannot show the back/legs clearly.

Use Mark start and Mark end to label on-back, upright, uncertain transition or not-visible intervals. Unmarked frames remain unscored; full-clip-viewed records coverage only. Export `Dyadic_posture_feasibility_scores_20261015.json`. Flailing is not assessed by these posture labels. Original candidate predictions are not displayed on the video, but this selection is not strictly blinded because its purpose and historical examples have been discussed.

Checks: all seven clips decode to 600 frames, global offsets are retained, source hashes are stored and viewer JS parses. Browser playback, one-frame stepping (4433 to 4434), and the offset-label toggle were verified on localhost:8793. A paused-frame callback race was corrected in this new viewer; PREVIEW.png records the visible result. Posture annotations remain unscored. Source science remains PSC 1.6.0 / processor 0.8.2-group. Next: obtain attributed visible-posture examples, compare raw feature evidence on positive and upright-control intervals, and test any revised screen on held-out recordings. No silent threshold fit or production promotion.

## VAF scores received and radio controls — October 15

The original `Dyadic_posture_feasibility_scores_20261015.json` is preserved byte-for-byte as `scores_VAF_20261015_original.json` in the evidence folder. All seven run identities, target IDs, frame bounds and source-video hashes match the selection manifest. Intervals are in bounds and nonoverlapping. `SCORE_IMPORT_20261015.json` records the import and original hash.

VAF marked clips 1, 2 and 4 on back for their full 600 frames each. Clip 5, the quiet ID 1 control, is labeled on back at 2724–3255 inclusive (532 frames); the remaining 68 frames are unscored, not an inferred recovery. In total there are 2,332 explicitly positive frames. The saved selection flags cover 600, 600 and 405 frames of clips 1, 2 and 4 and none of clip 5, giving 727 missed human-positive frames in this targeted set. These are rounded-viewer-coordinate selection masks, not an exact audit of production outputs or an unbiased sensitivity estimate.

Clips 3, 6 and 7 have overall negative assessments but no explicit negative intervals. Clip 3's note says this is fighting, not turtling. Only clip 7 has full-viewing coverage checked; none of these overall assessments is converted into 600 frame-level negatives. Clip 6's 131 selection flags are unsuppressed and its entire clip is on fungus; do not call those production false positives. Clip 7's selection mask was an all-zero placeholder, not a computed negative detector result.

The immediate development priorities are quiet on-back posture missed by movement criteria, incomplete candidate coverage in clip 4, and fighting that resembles turtling in clip 3. Do not suppress all social-contact frames: fighting and overturned posture may coexist. Confirm boundaries and visible posture before changing rules, then test on separate recordings. No classifier or production science was changed.

All five dropdowns in this reviewer are now radio controls. “Not turtling” replaces the displayed “Upright / false alarm example” label and is also an explicit interval option. Historical overall-assessment values remain compatible with existing exports; new negative intervals use `not_turtling`. Existing local storage is retained and copied to a separate pre-radio backup key on first load. The original exported scores and pre-radio HTML are preserved. Browser checks verified radio selection and clip navigation; RADIO_PREVIEW.png records the interface.
