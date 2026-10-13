# BA interpolation 1.0.0 — frozen for large-scale human QC

Vince approved freezing the speed-based interpolation trial and processing all verified compatible BA cells. The reconciled census selects 221 configurations from 14 recordings. These are cell windows, not 221 independent recordings. Each retains 7,200 inclusive global frames.

The rule fills bounded gaps of at most 30 missing frames when endpoint distance divided by elapsed frame steps is at most 20 original-image pixels/frame. Each endpoint needs another finite supporting point within 15 frames, with average support motion at most 25 pixels/frame. There is no total-distance cap. Filled positions must lie inside the arena. Human exclusions and their supporting intervals block filling; generated positions never become recursive anchors. The API requires explicit BA and exactly one animal. Dyadic/group pipelines are untouched.

The standalone module exactly reproduces all four prior transfer arrays. Seven focused regression tests pass. This establishes software parity, not biological validation. Three full-run verdicts were usable; new_021 was needs-work. Preserve that concern in review.

Inputs remain immutable. For the additional100 cohort, the previously generated recovery proposal is the baseline; for the older121, baseline is compatible raw tracking. All20 cells of Camera_1_40169154_20260627_1614_ACT2 use the independently verified light-exclusion rerun, with global1608–1609 protected. These cohorts are not equivalent recovery treatments. This batch freezes interpolation, not a new universal shadow-recovery method.

Large-batch evidence lives in outputs/ba_frozen_interpolation_all_20261013 and the same-named Firebird idtracker_pipeline_runs folder. PLAN.json enumerates sources and exclusions. Per-run COORDINATES.npz and FRAMES.csv distinguish raw, baseline, analysis, method, and human exclusions. MANIFEST.json records hashes and checks; QC.json records review priorities. Automatic outputs remain UNREVIEWED. Consult the release receipt for actual completion rather than inferring it from this plan.

## Handoff to turtling work

Use stable census_id plus source TOML, global frame, source hashes, and coordinate-layer version. Keep human posture labels separate from tracking review. Interpolation estimates a path; it does not observe posture, flailing, or true distance travelled. Turtling is NOT_ASSESSED in this batch. Do not reuse old masks as though recomputed on the new trajectories. Human-excluded frames remain unknown. Preserve BA060's documented missed episode and all attributed score conflicts.

## Handoff to the QC dashboard

Ingest PLAN.json, per-run QC.json/MANIFEST.json, and exported human scores. Missing percentage excludes deliberate exclusions from its denominator and reports exclusions separately. Remaining adjacent finite-coordinate jumps >=100 pixels, long gaps, outside-arena points and crop-brightness changes are triage signals, not automatic exclusions or calibrated confidence. A skim is not full-frame approval. Keep unreviewed, unsure, needs-review, and exclusion recommendation distinct. Never merge scores across changed dataset fingerprints silently.

Hannah and Savannah should skim traces first, open footage when needed, and record one run verdict plus brief category flags. The portable reviewer saves all run decisions together. The user will distribute the package; no collaborator messages or access changes are authorized by this handoff.
