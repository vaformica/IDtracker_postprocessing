# BA light blip: two-frame exclusion and tracking rerun

AI-written record by Codex, October 12, 2026. VAF directly identified original
frames **1608–1609 inclusive** in
`Camera_1_40169154_20260627_1614_ACT2.mp4` and authorized rerunning all its TOMLs
with only those frames excluded. This is a human-selected correction, not a
brightness-threshold exclusion or proof that all recording disturbances are solved.

All 20 source configurations A1–D5 are preserved. Derived copies change only
`tracking_intervals`. Nineteen use `[[1095,1608],[1610,9000]]`; C5 retains its
unusual original start of 10, using `[[10,1608],[1610,9000]]`. Endpoints in these
IDtracker intervals are exclusive. C5's start remains a separate review concern.
No other frame is removed. Original 7,200-frame analysis windows remain fixed,
with 7,198 eligible frames and two explicitly excluded observations. Do not
interpolate positions, displacement, or posture across the gap. Unexpected
tracking loss must use the eligible denominator and be reported separately.

Firebird root:
`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_light_exclusion_1608_1609_20261012`

`MANIFEST.json` records source paths/hashes, copied settings, original/revised
intervals, and VAF attribution. `SUBMISSION_RECEIPT.json` records Slurm array
**918316**, 20 jobs with four concurrent. All 20 source hashes and derived TOML
semantic comparisons passed before submission. Four interval helper tests pass.
Two preparation checks caught a path-type issue in a final print and an overly
uniform start assumption for C5; both were resolved before any job submission.
The already-correct derived C5 TOML was retained; originals were never edited.

The installed IDtracker reports 6.0.10 despite its environment name 6_0_14.
Inspection confirmed background sampling uses retained processing episodes.
Per-cell status verifies intervals, the global trajectory frame axis, unavailable
coordinates at both excluded frames, source preservation, and unexpected missing
positions. `BATCH_STATUS.json` is generated after all tracking tasks finish;
inspect its live result before claiming completion. Successful tracking is not
biological approval or proof that later lighting effects have disappeared.

The BA IDtracker notebook tab has a verified update recording the intervention,
video, frame convention, job, provenance, and unfinished whole-collection review.
The BA postprocessor still requires gap-aware support; no revised PDF/video or
behavioral analysis release has been generated. Preserve previous results.

Whole-collection scope remains broader than turtling: the census lists 299 main
configuration groups, of which 121 have analysis records, 100 have compatible
tracking but no confirmed analysis, and 78 need reconciliation or tracking.
These are configurations, not an established count of independent animals.

## Completed output audit — supersedes initial exit-code failure

All 20 jobs produced a Success log marker but returned IDtracker exit code 1.
The first audit therefore rejected them; it remains preserved. Independent
`OUTPUT_VALIDATION_v2.json` now verifies all 20 sessions, source/derived hashes,
9000-frame global arrays, requested intervals, and NaN coordinates at 1608–1609.
Status is OUTPUTS_VERIFIED_WITH_EXIT_WARNING_UNREVIEWED, not biological approval.
Unexpected missingness persists: D1 has 48.53%, C5 8.14%, and D4 2.00% of 7198
eligible observations missing. This two-frame intervention has not solved all
tracking issues. No downstream science or reports have been regenerated.
