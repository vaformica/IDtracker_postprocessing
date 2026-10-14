# One QC layer for BA, dyadic, and group videos

AI-written development record by Codex, October 12, 2026.

The immediate goal is to stop treating the BA review as only a turtling review.
A usable assessment must show whether the source recording was disturbed,
whether the animal was tracked, and whether the behavioral interpretation is
uncertain. These are different questions and should remain separate in both the
interface and the data.

The first implementation, `unified_qc.py` 0.1.0-development, adds a shared QC page
and JSON record to new BA and common dyadic/six-beetle pipeline runs. It checks
full-image brightness and translation at every original frame (reduced resolution),
missing positions and long gaps, adjacent-frame jumps, simultaneous jumps across
IDs, arena departures, and prolonged exact stationarity. Each flag identifies
its scope, animal when applicable, original frame range, and evidence. The page
provides raw position traces, a brightness trace, expandable reasons, and a link
to the existing synchronized video. No automatic flags change tracking or approve
behavior. Existing BA turtling and social PSC rules remain unchanged.

A content-hashed source-video cache allows different cells to reuse recording
screening. Skipped or failed scans are explicitly unknown, not clean. Intentional
exclusion support in the shared summary changes the denominator and breaks steps;
it does not complete the separate gap-aware production BA analysis work. The
20-cell 1608–1609 tracking rerun remains a separately attributed intervention.

Eleven focused checks cover lighting versus translation, local versus broad
brightness changes, one/two/six animals, unknown gaps, intentional exclusions,
input preservation, serialization, incomplete scanning, and no-overwrite reports.
The 266-test repository suite passed using the project environment plus the
existing TOML serializer. Initial environment-only failures (missing matplotlib
in the alternate runtime; missing toml in the project environment) were resolved
for verification without installing or changing the environments. An encoded
60-frame video with a two-frame flash produced transitions at frames 20 and 22,
correctly bracketing flash frames 20–21; one/two/six-animal report checks and
cache readback passed. A development serialization error was fixed before these
checks passed. These are software checks, not biological validation.

Full original-recording evaluation is retained under local/Firebird
`unified_qc_development_20261012`. Consult its live LIGHT_VIDEO_SUMMARY.json for
results; job 918336 scans the known lighting recording. Earlier failed job
918330 and its code are retained. No existing release has been overwritten.

Remaining work is substantive: calibrate source checks on human-reviewed BA,
dyadic and group disturbances/controls; aggregate sibling-cell evidence by video;
connect configuration/session mismatches and existing behavior/PSC ambiguity to
the common index; complete gap-aware science for reruns. The current checker
does not detect anatomical posture, guarantee identity, reliably classify people
or shadows, or flag every small camera motion. Low-resolution global screening
can miss local or gradual disturbances. A full all-BA audit remains unfinished.

Implementation and use: UNIFIED_QC_README.md. Pipeline entry points:
run_ba_pipeline.py, run_group_pipeline.py, run_six_beetle_pipeline.py. Shared
Firebird GUI deployment includes the module; old frozen batch snapshots and the
legacy standalone processor/GUI require explicit integration before claiming
coverage there. Full MP4/PDF regeneration was not performed in this task.

## Actual lighting-recording result

Job 918336 completed a scan of all 9000 source frames. Broad lighting candidates
occur at transitions 759, 767, 769, 781, and 2136; possible image-motion candidates
occur at 1087, 1091, and 1093. Many are outside the usual start of 1095 and must
not be counted as problems inside that analysis window. No broad brightness or
translation threshold fired at VAF's 1608–1609 interval: the low-resolution tile
medians were unchanged there. This disagreement remains unresolved; it could
reflect a local/subtle effect, insufficient thresholds, or a frame-reference
issue. The contemporaneous reviewer frame-step bug also warrants checking the
visual reference. Do not retract, expand, or overwrite VAF's attributed exclusion
based on this automatic result. The full-source result is a limitation test,
not validation of the checker. LIGHT_VIDEO_SUMMARY.json preserves the evidence.
