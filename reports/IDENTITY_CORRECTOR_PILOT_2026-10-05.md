# Identity corrector 0.2.0 — Box01 pilot

> **Current-status cross-reference (15 October 2026):** Six-beetle development is on hold until Charlotte needs network or time-on-fungus data. There is no automatic October 19 or two-week restart. See [the current handoff](../SIX_BEETLE_README.md). The dated report below is preserved as history; reminder and workflow statements are not current authorization. Outputs remain UNREVIEWED.

User-authorized first test of a click-based identity correction layer. Target: `groupagetrial04_062124_Box01_MIX`, global frames 175–9174, opening at 855. Scientific source remains PSC 1.6.0 / processor 0.8.2-group, UNREVIEWED. No biological corrections have been supplied or applied.

## Reviewer workflow

Open `START_HERE.html` in the portable case folder. Enter your name. Click the beetle with the wrong label (or select its current ID with the numbered buttons), then choose its correct ID. The operation exchanges both identity channels, including missing observations, instead of duplicating one animal.

Choose this frame, suggest a continuous interval, or set the first/last inclusive global frames manually. The suggested interval grows both backward and forward from the clicked frame, stopping if either selected identity is missing, is within 60 original-video pixels of another detected animal, jumps more than 100 pixels in one frame, or reaches the window edge. These are conservative coordinate gates, not detection-fragment or biological identity guarantees. Manual bounds can cross those gates, so the reviewer must inspect the whole interval.

Preview, scrub in both directions, accept, undo/redo, and compare original labels. Export the accepted corrections as a JSON file and return it to Codex for reprocessing. Import restores an exact-source log. Draft storage is best-effort browser-local; export is the portable save. A preview is never included unless accepted. Typing in fields does not trigger numeric identity shortcuts.

This prototype swaps two existing tracks and adds human PSC for missing IDs. It cannot create a missing detection, draw new coordinates, identify a fully occluded beetle, retrain IDtracker, or edit through IDtracker’s Validator. The browser displays corrected labels and the human PSC overlay; it does not show stale automatic PSC/behavior calculations as recomputed results.

## QC warnings

The Box01 raw input has 10 adjacent-frame steps over 100 original pixels and 48 returns whose displacement from the last finite observation exceeds 100 pixels across missing frames. The latter are separately identified and are not one-frame speed violations. The warning list seeks to the exact global frame; each report remains a review prompt, not proof of an identity error. A prior read-only scan found 23 of 51 regenerated cases with at least one adjacent raw jump over 100 pixels (104 total). Only Box01 has this new corrector package so far.

## Implementation and provenance

- `build_identity_corrector.py`: verifies canonical/video source hashes and emits new HTML/video packages without overwriting existing outputs. Full coordinate precision is retained.
- `identity_corrector_core.js`: immutable raw replay, ordered reciprocal swaps, jump/gap warnings, bounded interval proposals, coordinate projection for all supported review rotations.
- `identity_corrector_ui.js` and `identity_corrector_template.html`: click selection, clear preview/accept states, playback, interval bounds, undo/redo, import/export, optional local draft restore.
- `identity_corrections.py`: validates source hashes, IDs, ordered intervals, anchor membership, attribution, and duplicate action IDs; exports the original and corrected window, per-frame identity mapping and an audit receipt. With the exact original full trajectory, it also writes a new `human_corrected_trajectories.npy`; outside-window coordinates are unchanged. Stale ID-indexed confidence metadata is not copied.
- `processor.py` accepts that specific corrected filename only with its matching correction receipt and labels it HUMAN_IDENTITY_CORRECTED. The shared processor hashes that receipt as an input. PSC parameters and scientific algorithm version are unchanged.

Example replay (new output directory required):

```sh
venv-mac/bin/python identity_corrections.py \
  --bundle /path/to/original/analysis \
  --log /path/to/case__identity_corrections.json \
  --trajectory /path/to/original/trajectories.npy \
  --output /path/to/new/identity_corrected_input
```

Then use the existing shared pipeline with explicit `--trajectory /path/to/new/identity_corrected_input/human_corrected_trajectories.npy`, the original session/TOML/video and window/settings, and new analysis/review outputs. Recompute proximity, PSC, movement, CSVs/PDFs and review media after applying human identity corrections. Keep the original release and correction receipt alongside the new derived outputs. Do not call the whole video reviewed merely because some intervals were corrected.

## Validation

All 162 Python tests passed. New tests cover reciprocal and overlapping swaps, NaN/missing preservation, inclusive backward correction, unchanged source/outside-window data, exact hash binding, invalid IDs/intervals, duplicate decisions, full trajectory export, accepted source classification, and no-overwrite behavior. Node tests cover matching replay behavior, suggestions stopping at proximity, warning classification, and rotated geometry.

Browser checks passed for video loading/seek to global frame 855, actual centroid clicking, choosing the replacement identity, interval suggestion, manual 850–860 preview, accept, undo, redo, and JSON download. The downloaded browser test log replayed successfully through the Python backend. That deliberately arbitrary test is explicitly labeled SOFTWARE TEST ONLY and retained under `outputs/identity_corrector_pilot_20261005/software_test_only/`, never in the scientific release. No full scientific reprocessing has been run with a human correction because none has yet been supplied.

Portable package: `outputs/identity_corrector_pilot_20261005/v0_2_0_final/groupagetrial04_062124_Box01_MIX/`. Open the named HTML or START_HERE.html; keep the MP4 beside it. Native file-URL browser automation was blocked by the browser’s URL policy, so direct file-open behavior was not automated; localhost playback/export was verified.

## PSC / pile addition requested during the pilot

The same editor now has Identity swap and PSC / pile modes. Select the missing member ID, then select or click its partner. Choose either the detected partner’s presumed position (hollow PSC marker) or pile membership with unknown location (coordinate stays missing). Both use the same bounded preview/accept/undo/export workflow. A detected identity cannot be relabeled PSC. A located pile needs a detected partner throughout the interval. Human-marked PSC may rely on the reviewer’s video evidence; it is not automatically inferred merely from a disappearance.

Identity swaps run first, followed by PSC decisions in their recorded order. A later swap that would make an earlier PSC decision apply to a detected ID is rejected until that conflict is resolved. Corrected input arrays never contain PSC-inferred coordinates. They remain separate as human_psc_positions/human_psc_source in the audit NPZ.

After reprocessing the corrected identities, bind the PSC decisions to the new bundle with:

```sh
venv-mac/bin/python identity_corrections.py \
  --bundle /path/to/new/analysis \
  --bind-psc-from /path/to/new/identity_corrected_input \
  --output /path/to/new/psc_review.json
```

Binding verifies that the newly analyzed raw window exactly matches the corrected window, then writes the existing beetle-review-v1 format for apply_review_decisions.py. That tool can build the reviewed CSV/HTML layer. Rebuilding reviewed PDFs and a fully verified delivery remains part of processing the returned human decisions; the browser does not do this automatically.

Additional tests cover separate inferred coordinates, refusing PSC for detected identities, unknown-location piles, conflicts between swaps and PSC, and rebinding to the regenerated source. Browser tests at frame 855 previewed/accepted/undid ID 2 with partner 4 as a software example, rejected PSC on detected ID 1, and exported an unknown-location PSC decision. The exported PSC log replayed successfully in Python. All test decisions are labeled software-only; none are scientific annotations.

## Label visibility update: 0.2.1

The latest pilot is under `outputs/identity_corrector_pilot_20261005/v0_2_1/`. Raw IDtracker labels can be displayed separately from corrected labels. Hide all labels and trails clears every video overlay without changing decisions. Both controls were verified in the browser at global frame 855. The existing missing-ID PSC decisions remain available; broader automatic pile reassignment remains future work. JavaScript correction tests passed.

## Identity-only successor 0.3.0

User requested identity correction before reconsidering PSC piles. The UI now has no pile mode and explicitly rejects importing PSC decisions (legacy backend replay is retained). `Follow this beetle` automatically proposes a path when a replacement identity is selected. It starts from accepted corrections, walks backward and forward, and follows the two selected physical paths through clear reciprocal raw-ID reversals. It ranks candidates by 65% current displacement plus 35% constant-velocity prediction error, allows at most 100 px per adjacent frame, and requires a 20 px score advantage over a second candidate. Both affected paths must be unambiguous, with no other detection within 60 px. An already-missing counterpart can remain missing; its reappearance stops the proposal. A selected missing path, close encounter, third-ID transition, or earlier accepted correction stops extension. These are heuristic proposals, not validated biological identity confidence. There is no appearance model or interpolation through occlusion. Manual bounds remain explicit reciprocal swaps.

Each proposal can comprise several swap intervals, leaving portions where raw labels are already correct alone. Export uses existing swap decisions with batch IDs, so the Python backend replays the same result without schema changes. Undo/redo handles one saved proposal as a group. Green intervals show saved edits; dashed amber intervals show unsaved previews; clicking the timeline seeks. Saved edits are immediately used for overlays, trails, playback, and subsequent suggestions. Browser storage is a draft; JSON export remains the portable record. Original data and automatic science versions remain unchanged.

Validation: Node tests passed for forward/backward raw-label reversals, protection of saved intervals, missing counterparts, ambiguity, gaps, and immutable exact replay. Five Python correction tests passed. Browser test selected 0→3 at 855 (arbitrary SOFTWARE TEST ONLY), proposed 175–993, previewed, saved, scrubbed to 900, and played through the corrected interval. Green saved interval and corrected labels were visible; undo removed the test. No biological corrections have been supplied.

Current local package: `outputs/identity_corrector_pilot_20261005/v0_3_0_final/groupagetrial04_062124_Box01_MIX/`.

## Development paused at Vince's request — 5 October 2026

Do not continue correction-editor development until Vince resumes it. A one-time reminder is scheduled in this chat for 19 October at 09:00 America/New_York (`resume-beetle-identity-correction`). Resume with the identity-only 0.3.0 Box01 pilot and global frame 855, review real user corrections, then rerun PSC and assess remaining pile errors. No biological identity corrections have been accepted by Codex. The independent IDtracker Validator copy lives at `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/validator_box01_20261005/session_groupagetrial04_062124_Box01_MIX`; font-workaround instructions are in `outputs/idtracker_validator_pilot_20261005/FONT_WORKAROUND.txt`. Current authorized work is warning-guided repackaging of the 51 existing PSC 1.6.0 reviews, not further editor development or scientific reprocessing.
