# BA timed-candidate development

Implemented `ba_turtling.py` v0.1.0 and BA pipeline v0.2.0-ba. The existing detector
thresholds and mask are unchanged. The module accounts for inclusive candidate
bouts, seconds, detected-time fraction, longest bout, and missing tracking time.
The pipeline writes `turtling_bouts.json`, appends bout pages to its existing PDF,
and passes the same record to viewer v2. The HTML canvas overlays candidate status
and accumulated candidate time; the MP4 itself remains an unannotated crop.

Attributed viewer v2 exports distinguish confirmed overturned posture (including
quiet pauses), rejected posture, active flailing, uncertain posture, and notes.
`apply_ba_turtling_review.py` verifies source identity against a full BA bundle and
writes a new reviewed summary; it does not overwrite automatic results. Conflicting
posture labels are rejected, identical overlapping labels count once, and uncovered
time remains unresolved. Corrected PDFs are not automatically regenerated yet.

Development excerpts use the frozen September 29 baseline on full source windows,
then slice its frame masks so clip edges do not change classification. Firebird:
`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_development_v0_2_20261001`.
The first extraction job hit a verification executable path error; the corrected
job reused the encoded first clip, completed the second, and decoded/count-checked
both: 1,080 frames (36 s) and 960 frames (32 s). No source inputs were altered.

The transition excerpt spans global frames 6384–7463 in Camera 3 June 29 C3.
Candidates start at 6894; the prior negative clip 7 ends at 6923. This confirms
its 30 false-positive frames are the final second adjoining positive clip 1.
The second excerpt spans 5505–6464 in Camera 2 June 29 C3. It contains candidate
bouts 5645–6071 and 6082–6464, locating the 10 missed frames at 6072–6081.
Human transition labeling remains required before changing either boundary rule.

Validation: full suite 145 tests passed before two additional review-accounting
tests; all 10 BA-targeted tests subsequently passed. Both one-page supplemental
PDFs were rendered and visually inspected. Browser bout navigation selected
frame 6894 and showed 0.03 accumulated candidate seconds, matching inclusive
accounting. New full 7,200-frame pipeline bundles have not been released; these
are development excerpts, and independent-video validation remains pending.
