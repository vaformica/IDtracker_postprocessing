# Frozen BA tracking: 221-cell review handoff

We have applied the frozen BA-only interpolation rules to all 221 verified compatible cell configurations across 14 recordings. Each window retains 7,200 original global frames. This is a tracking/QC delivery for human review, not a new behavioral analysis release.

The batch fills 1,910 short gaps, adding 6,711 explicitly interpolated positions. It leaves 11,370 unexpectedly missing positions and all 40 deliberately excluded observations (two frames in each of 20 cells). Thirty-three runs retain 490 adjacent-frame jumps of at least 100 pixels. Those runs rise in the review queue; they are not automatically excluded.

Original videos, source TOMLs, tracking, previous outputs and human decisions remain unchanged. All 14 original video hashes match earlier source records. The 100 additional cells retain their earlier recovery proposals as baseline; the 121 earlier cells use compatible raw tracking. This is not a new universal application of shadow recovery. Every run records its input history. New interpolation never changes finite baseline coordinates.

## Review materials

The portable set is `Downloads/BA_frozen_221_QC/START_HERE.html`, with the full shareable ZIP intended at `Downloads/BA_frozen_221_QC.zip`. Extract the entire ZIP before use. Traces are visible by default; video controls sit below the image. Reviewers can filter remaining jumps, high missingness, and unscored runs. One JSON download contains all their decisions, with name, coverage, verdict, flags and optional notes. Conflicting imports are rejected rather than overwritten.

Hannah and Savannah should start by skimming traces, then open footage when needed. A usable trace skim does not approve unseen frames. The earlier needs-work verdict for new_021 and C5's unusual start at frame 10 remain explicit warnings. No messages or access changes were made on their behalf.

## For the turtling chat

The new batch intentionally sets turtling to NOT_ASSESSED. Preserve existing human posture labels, the BA060 missed-episode finding and earlier annotation conflicts. Interpolation estimates a path; it does not observe posture or flailing. Use images/raw tracking and explicit uncertainty when assessing interpolated or missing periods. Do not silently reuse old masks as updated results.

Each `runs/<id>/COORDINATES.npz` contains `raw`, `baseline`, `analysis`, `method`, `protected`, `start`, and `end`. Coordinates are in original-image pixels. Local index i corresponds to global start+i. `FRAMES.csv` provides the same layers in a readable table. Methods distinguish existing, prior_recovery, interpolated, missing, and human_exclusion. Human-excluded frames remain unknown and cannot support interpolation.

## For the QC dashboard chat

Use PLAN.json and census_id for source identity; original TOML stem and run ID remain available. Read QC_INDEX.json for ranked runs, per-run QC.json/GAPS.json for evidence, MANIFEST.json for input/output hashes, and RELEASE_RECEIPT.json/PACKAGE_RECEIPT.json for completion. Scores use schema `ba-frozen-tracking-qc-v1`, bound to the dataset fingerprint. Preserve attribution and inspected scope; blank or unsure is never negative/approved. Keep human exclusion recommendations separate from applied exclusions.

Unexpected missing percentage excludes deliberate exclusions from its denominator. Brightness candidates are simple crop-median changes, not confirmed lights/shadows or a substitute for the separate unified source QC checker. Review rank is a triage heuristic, not confidence. The separate strict-jump/turtling preview and final dashboard are not overwritten. Movement summaries should not silently treat remaining major tracking errors as valid movement.

## Verification and frozen source

The interpolation module is version 1.0.0 (commit c20c8be). Reviewer/packaging changes through dfc1200 leave those rules unchanged. CODE_FREEZE.json records exact source hashes. All 306 repository tests passed; the four earlier transfer arrays replay exactly. Independent local checks reproduce all 221 new arrays, verify 1,768 per-run file hashes and all 1,591,200 CSV frame rows. Every review video decoded to 7,200 frames on Firebird. Browser playback has not been tool-verified.

The authoritative Firebird folder is `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_frozen_interpolation_all_20261013`; local evidence is the same-named folder under outputs. Representative alignment and ZIP verification are the final release gates; consult their receipts for their actual status. All automatic results remain UNREVIEWED.
