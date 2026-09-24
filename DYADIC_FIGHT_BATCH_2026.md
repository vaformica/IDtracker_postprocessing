# 2026 dyadic fight batch

The Firebird batch is at
`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_fight_review_20260923_1940utc`.
The immutable source and submitted TOMLs, per-run receipts, logs, IDtracker
sessions, corrected analysis, review files, and quality metrics live under
`tasks/<task-id>/`. Nothing in the student source directories is overwritten.

The read-only inventory found 117 TOML files. Thirteen were byte-identical
copies, leaving 100 distinct eligible two-beetle configurations and four
structural exclusions. The excluded TOMLs are listed in
`reports/exceptions.json`: one requested three animals and three supplied
only an arena ROI rather than an arena plus one fungus ROI. The 100 staged
configurations passed an additional ROI geometry check; its flags are recorded
in `reports/toml_geometry_qc.csv`. Geometry checks cannot establish that a
fungus was labeled correctly or that identities remain correct in a fight.

Every submitted configuration preserves the student's settings and frame
interval except `use_bkg`, which is set to true in a separate immutable copy.
The original TOML and SHA-256, submitted TOML and SHA-256, and all source
paths are retained in `plan.json` and each task receipt. Twenty-three distinct
configurations have an existing trajectory session with an exact match to
their background-on settings; those sessions are reused. The other 77 are
submitted to IDtracker 6.0.10 on Firebird GPUs. Reuse is reported separately
from new tracking, and all 100 receive a fresh corrected analysis and review.

IDtracker's TOML `tracking_intervals` end is exclusive. The group processor's
`--end` is inclusive, so final processing uses `end_exclusive - 1`, clamped
to the last available trajectory frame. The exact submitted and processed
intervals are recorded in `final_status.json`. Earlier preliminary analysis
attempts used the end directly; some failed at the trajectory boundary.
Those preliminary outputs are retained for provenance but never counted as
the final result. The reusable `dyadic_batch_worker.py` has also been fixed
for future runs.

`analysis_final/` contains the PDF, frame-by-frame location and state CSVs,
fungus summaries, event tables, and manifest. `review_final/` contains the
interactive HTML and synchronized video. Both use the shared persistent-pile
model version 1.2.0. PSC positions are inferred only when supported by a
detected blob; a pile with no detection remains missing. Every output is
marked **UNREVIEWED** until a human checks the fight and any ambiguous IDs.

`quality_final.json` and `reports/beetle_quality.csv` give each beetle's raw
IDtracker missing percentage, the percentage after rejecting implausible
assignments but before PSC, and the percentage after detected-blob PSC
positions are included. The report also gives PSC coverage, independent
assignments, unresolved pile frames, longest gaps, >100-pixel raw frame jumps,
and IDtracker's exported identity-score mean, median, and low-score fraction.
These identity scores are algorithmic self-scores, **not calibrated
probabilities of correct identity**. The batch report also carries the
session-level IDtracker estimated accuracy and silhouette score.

During unattended tracking, two student TOMLs set `check_segmentation=true`.
IDtracker stopped after 2-3 frames with extra blobs. The recovery runs use
separate, hashed TOML copies with only that interactive stop flag set to false;
the segmentation thresholds and all other settings stay the same. Their
original failed outputs and logs remain available. A third Testing TOML
(`Camera_1_40169154_20260630_1342_FIGHT_ACT1__cell01`) was excluded from
review production because IDtracker detected zero animal blobs with its
original thresholds and requested background subtraction. It has no trajectory
to analyze, so no PDF or identity score is invented. Its receipt and log are
retained for later, separately labeled threshold work.

`dyadic_batch_collect.py` counts a task as complete only when its corrected
`final_status.json` says `COMPLETE_UNREVIEWED`. After all runs resolve,
`dyadic_batch_package.py` creates a portable ZIP containing each completed
source and submitted TOML, PDF, CSVs, quality file, HTML, and compact review
video, plus the documented exclusion and its logs. The
compact MP4 preserves the original frame count and frame rate; the corrected
sample retained all 8,241 review frames at 30 fps. Source video and full-resolution
IDtracker trajectories remain on Firebird.
