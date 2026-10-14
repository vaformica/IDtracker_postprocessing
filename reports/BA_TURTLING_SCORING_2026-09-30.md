# BA turtling scoring set, September 30, 2026

User authorized preparation of a blinded scoring set before classifier calibration.
The new Firebird root is `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_scoring_v0_1_20260930`.
Local review artifacts are under ignored `outputs/ba_turtling_scoring_20260930/`.
Consult `VERIFICATION.json` for completion; human labels remain UNREVIEWED.

The set contains 18 twelve-second arena crops: six passages from each of two
previously user-highlighted C3 runs and one pilot B1 run. Per source, three
non-overlapping passages prioritize the frozen baseline's candidate-frame count,
then absolute heading change divided by one plus spatial extent. Three other
non-overlapping passages are selected randomly from remaining windows. Both
selection and shuffled display order use seed 20260930. These are exploratory
ranking features, not a new validated detector. Random passages are not known
negatives. Candidate enrichment prevents interpreting prevalence as population
prevalence. The ambiguous historical A1 session remains deferred.

The baseline is imported from the preserved September 29 BA pilot code snapshot.
Each 7,200-frame source window begins at the source TOML tracking start. Crops
retain source orientation, have 12 pixels of arena padding, and contain 360
frames at verified 30 fps. The first extraction attempt was canceled for efficiency
and its partial output retained under `attempt_1`; the replacement uses accurate
input seeking to integer seconds followed by residual-frame trimming.

`build.py`, `verify.py`, source hashes, frame bounds, crop geometry, baseline
counts, selection reasons, and clip checksums are saved in the Firebird root.
`selection_key.json` is an analyst key, excluded from the review ZIP and page.
The page collects reviewer identity, separate overturned/flailing judgments,
multiple optional clip-relative time intervals, uncertainty, and notes. Browser
storage is a convenience; exported JSON is the portable annotation record.

No automatic scientific release or shared detector was modified. This set is for
initial label collection; held-out-video evaluation and detector calibration
remain pending annotations. Short clips can truncate events, so event-duration
validation will also require longer context around confirmed positives.
