# Current handoff for future Codex tasks

**Current six-beetle status — 15 October 2026: ON HOLD.** Vince put six-beetle development on hold on October 14–15 because tracking is unreliable and correcting obscured piles takes too much time. Revisit when Charlotte needs network or time-on-fungus data; there is **no automatic October 19 or two-week restart**. Dyadic and BA work continue separately. Contact versus touching/mounting definitions remain deferred. See [Charlotte’s current handoff](SIX_BEETLE_README.md) for review limitations, sources, and the unresolved 26/28/30 count mapping.

Read [README.md](README.md) and [reports/PROJECT_HANDOFF_2026-09-28.md](reports/PROJECT_HANDOFF_2026-09-28.md) before changing the pipeline. This file records the 2026-09-28 checkpoint; verify live Firebird state for later work.

- **Current science versions:** `persistent_groups.py` has PSC model **1.5.1**; `six_beetle_processor.py` has script **0.8.1-group**. The same module and parameters serve dyads and six-beetle runs. `processor.py` and root `VERSION=0.8.1` describe the older standalone prototype.
- **Review outputs:** raw/PSC comparison viewer **v3** and outlined PSC track PDFs **outlined-psc-v1**. A presumed position needs compatible detection evidence; unresolved beetles stay missing. Human edits are separate, attributed outputs. Never present automatic PSC as directly observed.
- **Latest official GroupTrial:** 26 2024 six-beetle trials, 9,000 inclusive frames each from its TOML tracking start, in `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/grouptrial_2024_9000_frames_OFFICIAL_26_psc_v1_5_1_processor_0_8_1_20260928`. Full and per-box ZIPs; full ZIP SHA-256 `3b05174855d82efe619116e2a14876ba5ddf8b7953cc74c47928f42a77ab2c4f`.
- **Latest official dyadic:** 99 eligible 2026 fights, 7,200 inclusive frames each from its TOML tracking start, in `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_fight_7200_frames_psc_v1_5_1_processor_0_8_1_20260928`. Full ZIP and `individual_run_zips/` with 99 per-run bundles; full ZIP SHA-256 `2064ff0d95b2774da35f94122080d7842d02ae7f25f413aa88bb5cc76524f66b`. Four incompatible TOMLs and one no-blob TOML excluded.
- **Scientific status:** all automatic releases above are `UNREVIEWED`. Compare raw and PSC video, inspect conflicts/uncertainty, and export attributed review decisions before calling a result approved.
- **Evidence:** per-run `analysis/manifest.json`, batch `RELEASE_RECEIPT.json`, `PROCESSOR_PARITY.json`, and ZIP checksums are authoritative. The small local copies are under ignored `outputs/`. Source TOMLs and IDtracker tracking are immutable inputs; use new versioned output roots.
- **Run path:** `group_firebird_gui.py` (all supported groups), `dyadic_firebird_gui.py` (dyad filter), `idtracker_toml_gui.py` (tracking submission), or `run_group_pipeline.py --help`. See `GROUP_PIPELINE_README.md`. Batch release scripts remain in the repo root for reproducibility; don't assume one batch's paths apply to another.
- **Checks:** `venv-mac/bin/python -m unittest discover -s tests -v` passed 133 tests on 2026-09-28. Before any new release, verify hashes, inclusive frame windows, every MP4's encoded frame count, PDF versions, raw/PSC CSVs, ZIP integrity, and explicit review status. Do not infer biological validity from tests alone.
- **Repository hygiene:** Git ignores new `outputs/`, `tmp/`, `derived_videos/`, annotations, caches, and ZIPs. Preserve local and remote research data and provenance. Do not prune Git history or delete withdrawn/old analysis folders without a data-specific audit.

## BA pilot addition (2026-09-29 UTC)

`run_ba_pipeline.py` adds one-animal, one-arena BA bundles using the existing standalone `processor.py` BA metrics/PDF renderer, not social PSC. Default is 7,200 inclusive observations from the source TOML start. See `BA_PIPELINE_README.md`. `ba_inventory.py` records source/session matching and selects six source videos with seed 20260929 before QC exclusions. `ba_pilot_batch.py` and `ba_organize_pilot.py` produce new run folders, per-run ZIPs, indexes, and a candidate/control turtling review worksheet. Pilot root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_2026_7200frames_pilot_v0_1_0_20260929`; inspect its live `RELEASE_RECEIPT.json` for completion status. All outputs remain UNREVIEWED. Provisional QC flags are not exclusion rules. `reports/BA_TURTLING_DETECTOR_REVIEW_2026-09-29.md` documents a demonstrated limitation of the old detector and a proposed validation workflow; no new turtling classifier has been validated.

## Dyadic review correction under development (2026-09-29)

Local `persistent_groups.py` is now **1.5.2**, and `build_canonical_review.py` emits viewer **v4**. Neither has been released to Firebird. The official releases above remain 1.5.1/v3. Read `reports/DYADIC_PARITY_AUDIT_2026-09-29.md` before new releases. New contacts require fresh proximity within the social radius (60 px by default), independently of movement gates. Pass `--source-toml` to the shared pipeline to identify the cell and name HTML, MP4, regular PDF, and derived outlined PDF from its original stem. Historical version-specific release/packaging scripts retain old assumptions and require a new versioned successor before reuse.

Later checkpoint (2026-09-30): **The authorized 25-run PSC 1.5.2/viewer v4 development pilot is COMPLETE_UNREVIEWED**, not a full scientific release. See `reports/DYADIC_PILOT25_2026-09-30.md`. The new root is `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_25_run_development_psc_v1_5_2_viewer_v4_20260930`. Seed 20260930 covers all 12 source recordings; A1/B2 of the reported recording are targeted cases. All 25 MP4 frame counts, 50 PDF versions, raw/PSC CSVs and ZIP integrity checks passed. Local `outputs/dyadic_pilot25_20260930/review_set/START_HERE.html` links the expanded files; 775 run-file hashes and 31 code-file hashes were verified. Full remote ZIP SHA-256: `95525992d1b4f5c8be35aa7e1dc1f5bc80b39886ada005c9e32436c229955c23`. **Exact reported cell/frame reference remains unconfirmed**: both A1/B2 retain PSC at global frame 3005, but extracted images show the beetles appearing close together. Retained labels alone do not prove the reported error persists; confirm global versus review-video frame numbering. Do not resubmit into existing run directories. `dyadic_pilot25.py` and `dyadic_pilot25_package.py` are the new reproducible drivers; the remote analysis snapshot is frozen and hashed.

## Dyadic output withdrawal (2026-09-30)

Vince requested deletion of the 99-run PSC 1.5.1 derived output set. Deleted and verified absent: 5,051 files on Firebird (official 7,200-frame set plus earlier 1.5.1 outputs and ZIPs) and 2,278 files from the local downloaded package. Original source videos/TOMLs, submitted TOMLs, IDtracker tracking, detection evidence, code snapshots, and JSON/Markdown provenance remain. Prior release receipts/statuses are historical and marked withdrawn. Deletion manifests and receipts: remote `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_withdrawal_20260930/`; local `outputs/dyadic_withdrawal_20260930/`. All 297 referenced remote source-file records were checked unchanged. The replacement 25-run development sample is now complete as recorded above.

## Hannah review correction (2026-10-05)

Current development code is **PSC 1.6.0 / group processor 0.8.2-group**. Read
`reports/DYADIC_RAW_ID_PRIORITY_2026-10-05.md`. Every available IDtracker x/y stays
`ASSIGNED` at exactly its input position, even on a shared blob or immediately
after reappearance. Proximity is <=60 original-image pixels between assigned
centroids. PSC inference is allowed only for missing IDs with proximity and
compatible detection support. Split/distant confirmation parameters are accepted
but inactive; raw jumps are retained as coordinates and filtered separately from
movement summaries. Do not silently correct upstream swaps. Both dyadic and
six-beetle routes share these rules.

A new read-only-input replay of all 25 dyadic and 26 six-beetle runs found zero
available-ID assignment changes under 1.6.0; all 51 result hashes were verified.
Evidence: `outputs/psc_raw_priority_audit_20261005/` locally and
`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/psc_raw_priority_audit_20261005/`
on Firebird. Existing review videos/PDFs remain their prior versions and have
not been regenerated. This is software regression evidence, not biological
approval. Hannah’s C1 frame 6571 missing-ID inference and Wrong A2 frame 3071
identity swap remain unresolved review matters; C1 6780/6865 lie outside 60 px.

Validation for the 2026-10-05 correction: **157 tests passed**, including shared
pipeline export states and release gates. Test log and code hashes are in the
local regression audit folder.


## Regeneration and collaborator access (2026-10-05)

The previous statement that videos/PDFs were not regenerated is superseded: all 25 dyadic and 26 six-beetle runs are now COMPLETE_UNREVIEWED under PSC 1.6.0 / processor 0.8.2-group. Authoritative Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/psc_1_6_0_regenerated_51_20261005`. Local index: `outputs/psc_regenerated_51_20261005/review_set/START_HERE.html`. See `reports/PSC_1_6_0_REGENERATION_2026-10-05.md` for validation, sharing, and withdrawal receipts. Private Dropbox viewer access with downloads was granted to Hannah Donald and Charlotte Greene. Original inputs and provenance remain protected; historical release receipts are retained unchanged.

## Correction development paused (2026-10-05)

Vince requested that correction-editor development be tabled. Latest identity-only editor is 0.3.0; see `reports/IDENTITY_CORRECTOR_PILOT_2026-10-05.md`. A one-time reminder is set for October 19, 09:00 local. Do not infer permission to resume editor development from review-packaging work. Current follow-up adds raw-jump and other human-review warning sidecars/indexes to all 25 dyadic and 26 six-beetle PSC 1.6.0 packages; it does not change scientific trajectories or PSC rules.

Warning packaging is now COMPLETE_UNREVIEWED: local and Firebird root `psc_review_qc_20261005`, with 51 new `QCwarnings_v1` individual ZIPs in the existing shared Dropbox folder. See `reports/REVIEW_WARNINGS_2026-10-05.md` and `QC_DELIVERY_RECEIPT.json`. The canonical Dropbox START_HERE now links the warning-guided downloads; the prior page is retained as `START_HERE_before_QCwarnings_20261005.html`. Source science remains PSC 1.6.0 / processor 0.8.2-group. Raw adjacent-frame jumps >100 px: 101 across 20/26 six-beetle trials, three across 3/25 dyadic cases. These are review priorities, not confirmed ID errors.

## BA turtling recovery-gate development (2026-10-06)

Read `reports/BA_TURTLING_RECOVERY_GATE_2026-10-06.md` and the preceding
`reports/BA_TURTLING_REVISION_2026-10-06.md` before continuing BA turtling work.
VAF's final Run 1 annotation is **2834-8294 inclusive**, with no turtling before
2834. The briefly stated 1177 onset was retracted without changing score files.
VAF attributes the early tracking jumps to a camera bump and states that all
BA animals begin in death feint. Camera displacement is not animal movement.

Separate development modules `ba_turtling_episode_experiment.py` (0.2.0) and
`ba_turtling_recovery_gate.py` (0.1.0) are not production defaults. The latter
tests a 30-pixel departure sustained for 30 observations; known initial camera
artifacts require reference reacquisition first. This does not replace the
prototype's exact-start continuous-chain wake metric. In the 12 scored runs,
the gate removes Run 1's 149-frame false event without removing true detections;
253 missed frames remain. These scored runs informed development, not independent
validation. Ten gate tests passed. Preserve all original scores and prior outputs.
Evidence root locally and under Firebird's `idtracker_pipeline_runs/`:
`ba_turtling_recovery_gate_20261006`. The earlier six new-source validation clips
have not been re-evaluated under these revisions. No full BA release is approved.

### Run 12 human-score correction (2026-10-06)

VAF additionally confirmed Run 12 posture at **2908-3036 inclusive**. The detector
already covered all 129 frames. Latest attributed scores and 12-run graph are in
`outputs/ba_turtling_run12_correction_20261006/` and the same-named Firebird folder.
Read `reports/BA_TURTLING_RUN12_CORRECTION_2026-10-06.md`. Extra frames are now
110 across the 12 runs; missed frames remain 253. Predictions and rules are
unchanged. Flailing during this added interval was not assessed and must not be
inferred from the new posture label. Earlier scores/charts remain historical.

### BA streamlined review ready (2026-10-06)

VAF agreed to another small review before broad BA processing. See
`reports/BA_TURTLING_QUICK_REVIEW_2026-10-06.md`. The frozen 0.2.0 episode +
0.1.0 recovery rules produced a five-clip scorer: two full blind runs, one
candidate scene, and two unflagged controls (nine minutes). Fourteen unused
runs were selected with seed 202610062; one failed tracking completeness and
was retained as blocked. Only one candidate episode occurred in the usable
short-scene pool. One full run comes from a new recording; other displayed
cells are new but their recordings were previously represented.

Local/Firebird evidence root: `ba_turtling_streamlined_review_20261006`.
Portable Downloads file: `BA_quick_turtling_review_20261006/START_HERE.html`.
Five encoded frame counts/media hashes and 22 scorer checks passed; browser
playback and biological validity are not established by those checks. Await
`ba-guided-turtling-review-v1` scores. Honor displayed-only scope, explicit
completeness, unsure/null labels, and flailing-not-assessed. Do not count blank
clips or unseen portions as negative. No broad BA/IDtracker batch was started.

### BA quick-review scores received (2026-10-07)

All five VAF decisions are complete. Clips 1–4 have explicit no-turtling labels;
clip 5 has posture 7010–7459 inclusive. Frozen predictions match all 16,200
displayed frames: TP 450, TN 15,750, FP 0, FN 0. This is a small guided check,
not broad validation. The positive interval reaches the clip boundary, so
continuation after 7459 remains unreviewed; flailing remains unassessed.
Read `reports/BA_TURTLING_QUICK_REVIEW_RESULTS_2026-10-07.md`. Evidence root:
`ba_turtling_quick_review_results_20261007` locally under `outputs/` and on
Firebird under `idtracker_pipeline_runs/`. Preserve the original export and
old predictions. No rule changes or broad BA batch were triggered by these scores.

### BA 100-run marked-review pilot (2026-10-07)

The authorized larger BA pilot is COMPLETE_UNREVIEWED. Read
`reports/BA_LARGE_REVIEW_PILOT_2026-10-07.md`. All 100 unused selected cells
across 14 previously represented recordings completed, plus a separate
previous-event follow-up. Twenty-two new runs have candidates; ten have QC
flags. Missing tracking and unconfirmed recovery remain review concerns, not
negative posture labels or automatic exclusions. Episode 0.2.0-development and
recovery gate 0.1.0-development remain frozen; production defaults are unchanged.

Local/Firebird root: `ba_large_review_pilot_20261007` under `outputs/` and
`idtracker_pipeline_runs/`. `CURRENT_RELEASE.json` points to the current
`review_v2/START_HERE.html`, `RELEASE_RECEIPT_v2.json`, and
`individual_run_zips_v2/`; earlier packaging is preserved as superseded.
Full analyses are in `runs_v2/`. Downloads: `BA_100_run_review_20261007/START_HERE.html`.
Four embedded-video rounds contain 60 clips and 38.03 minutes of footage,
including four preselected complete runs, 49 candidate scenes, two QC scenes,
four unflagged controls, and prior-event continuation at 7310–8738. Scoring
exports `ba-guided-turtling-review-v1` with scorer 1.1.0. Respect displayed
coverage, unknown/unsure states, and flailing-not-assessed; do not extrapolate
short-scene decisions. BA001 and BA004 had potential prediction exposure from
setup PDF previews, so do not treat all four full runs as strictly blinded.

Checks passed for 101 full-video frame counts, all 60 excerpt/media hashes,
100 report PDFs, 101 per-run ZIPs, 27 scorer checks and nine frame-alignment
cases. Representative PDF/video samples were visually inspected. No broad
biological approval follows from these checks. The dyadic turtling extension
is deferred, and social PSC/paused identity-editor work was not changed.

### BA quiet-posture / circling refinement (2026-10-07)

All four 100-run pilot score exports were imported: 60 complete VAF decisions,
68,453 displayed frames, including the separate prior-event follow-up. Read
`reports/BA_TURTLING_CONTINUITY_REFINEMENT_2026-10-07.md`. Labels apply only to
shown footage; keep guided, hidden/exposed full runs, controls, QC and follow-up
separate. Flailing remains unassessed. Frozen results and original scores remain.

New separate `ba_turtling_continuity_experiment.py` **0.3.0-development** filters
smooth/short loop anchors into an explicit ambiguous-review state and extends
localized quiet tails from a fixed last-anchor reference. It does not modify
production or the death-feint gate, fill missing coordinates, or establish posture.
In the 60 scored clips, FP falls from 1,125 to 57 frames and FN from 1,972 to 370;
3 FN are tracking-missing. Seven entirely rejected candidate scenes lose flags.
Earlier 12-run FN becomes 0 and FP 99 (from 253/110); the earlier five clips remain
unchanged. Threshold sensitivity is substantial: these are development fits,
not independent validation. Quiet upright stops and onset timing remain risks.

Local/Firebird evidence root: `ba_turtling_refinement_20261007` under `outputs/`
and `idtracker_pipeline_runs/`. Downloads viewer: `BA_turtling_refinement_20261007/START_HERE.html`.
It shows seven before/after examples including residual errors. Twelve tests pass;
video bytes/frame counts and viewer helper checks pass; browser playback was not
tool-tested. No broad release or dyadic turtling test was started. Original pilot
release pointers and reports remain historical frozen results, not revised totals.

### BA boundary refinement and fresh test (2026-10-07)

Read `reports/BA_TURTLING_BOUNDARIES_AND_IMAGE_TEST_2026-10-07.md`. Separate
`ba_turtling_boundary_experiment.py` **0.4.0-development** searches backward from
supported events and trims endings with sustained directed departure. It retains
0.3 quiet-tail/circling rules and the recovery gate; production defaults are unchanged.
Latest 60 scored clips: 427 to 26 disagreements (23 extra, 3 tracking-missing
positive frames). Earlier 12 runs: 99 to 54, including one newly missed endpoint
frame. Earlier five-clip check remains unchanged. These are development fits.
Simple image-feature classifiers failed recording-held-out comparisons and are
not used. BA060's new onset reaches the backward-search cap and remains uncertain.

Twenty unused cells from ten previously represented recordings were processed
with frozen code and existing tracking; no new IDtracker jobs. Nine-clip scorer
(7.79 minutes) includes eight fresh-cell clips and one earlier-source follow-up.
Five fresh clips and the follow-up hide predictions. Await attributed scores;
this is a new-cell check, not an independent-recording or population accuracy test.
Keep follow-up overlap separate and never count unseen/blank/unsure as negative.
Local/Firebird evidence root: `ba_turtling_boundary_image_20261007` under `outputs/`
and `idtracker_pipeline_runs/`. Downloads: `BA_boundary_validation_20261007/START_HERE.html`;
expected export: `BA_boundary_validation_scores_20261007.json`. Before/after examples
are in `BEFORE_AFTER.html`. Original scores and prior predictions remain unchanged.

### BA boundary-test scores received (2026-10-07)

All nine VAF decisions are complete; read
`reports/BA_TURTLING_BOUNDARY_VALIDATION_RESULTS_2026-10-07.md`. Frozen 0.4 versus
0.3 improves the eight fresh clips from 178 to 146 disagreements / 13,117 frames
(1.36% to 1.11%): 146 extra flags, no missed positive frames. Hidden clips have
146 / 10,417 disagreements; guided clips have zero / 2,700. These are targeted
new-cell results from previously represented recordings, not population accuracy.

Clip 2 (`fresh_06`) is VAF-labeled negative with an attributed broken-leg note
and recommendation to exclude from training. Keep this recommendation separate;
no training/exclusion was performed. It contributes 129 extra frames. Excluding
it post hoc leaves 17 / 12,217 errors (0.14%); retain it in the primary result.
Clip 3 remains flagged 6359–6375 after VAF's last on-back frame 6358.
One tracking-missing negative frame (Clip 1, 6863) stays unknown to the detector.

Separate earlier-source Clip 9 (`ba_060`) is on back throughout 6600–7499;
0.4 misses 6600–6909 (310 frames). Its capped onset 6910 is not a true flip;
true onset is at or before 6600 and unresolved. Keep its 7060–7499 overlap with
prior scoring separate; do not double-count or merge it into fresh validation.
No detector changes or production promotion followed this import. Evidence root:
`ba_boundary_validation_results_20261007` under local `outputs/` and Firebird
`idtracker_pipeline_runs/`. Original scores, frozen masks, and earlier reports remain.

### Encounter/orientation feasibility pilot (2026-10-09)

VAF requested visualizations on good-quality dyadic and six-beetle videos.
The separate four-video pilot is COMPLETE_UNREVIEWED; read
`reports/ENCOUNTER_ORIENTATION_PILOT_2026-10-09.md`. Local and Firebird root:
`encounter_orientation_pilot_20261009`, with `review_set/START_HERE.html`.
Two recordings per collection retain existing full videos and raw coordinates.
Silhouette axes are undirected, not anatomical head estimates. The optional
motion-aligned end assumes forward travel. Motion requires unique individual
blob support throughout the window; no gaps or PSC positions are filled.
The 85 proximity bouts yield 9 approach and 7 departure attributions stable
across three motion windows; these counts are not human validation and can
overlap by bout. Good QC does not prove identity, and the first dyadic example
has no stable attributions. Seven focused tests, four full encoded frame counts,
video/source hashes, link checks, and browser playback passed. Production PSC,
BA, and paused identity-editor development remain unchanged. Do not promote
the pilot's thresholds without an attributed biological evaluation.

### BA QC priorities and manual review dashboard (2026-10-12)

Read `reports/BA_REVIEW_PRIORITIES_2026-10-12.md`. Separate
`ba_review_priority.py` 0.1.0 produces sidecars for all 121 existing windows
(100 pilot + earlier-source follow-up + 20 boundary-test cells), not a new
tracking batch. Frozen 0.4 masks and raw coordinates are unchanged. Dashboard:
`Downloads/BA_review_priorities_20261012/START_HERE.html`. Evidence root:
`ba_review_priorities_20261012` under local `outputs/` and Firebird
`idtracker_pipeline_runs/`. Build 918305 completed after correcting cohort lookup
for the separately named historical follow-up; failed build 918303 is preserved.

29 runs are high priority, 35 have other checks, 57 have no automatic flags.
Flags are triage heuristics, never exclusions or calibrated confidence. Display
missing/gap/jump measurements, candidate durations, ambiguous/continuation/version
signals and human coverage separately. Human scores cover 82,030 / 871,200 frames;
overlap counted once. Manual export `BA_review_flags_20261012.json` records requests
and notes only. It cannot approve trajectories or rewrite biological labels.

The dashboard links existing scored footage and the unchanged two-scene boundary
review (6,249 frames); it does not contain full videos for every run. Await
`BA_focused_boundary_scores_20261009.json` from VAF; do not infer flip timing from
the search limit. 14 QC tests, 14 flag/export checks and dashboard script checks
passed. Browser rendering/playback is not established by these tests. No new BA
TOML batch, detector fit, or production PDF/video regeneration occurred here.

### Focused BA boundary scores received (2026-10-12)

Read `reports/BA_FOCUSED_BOUNDARY_RESULTS_2026-10-12.md`. Both VAF decisions
are complete. BA060 flips at 3942; combined displayed scores confirm 3942–7499
on back. Frozen 0.4 begins at 6910 and misses 3942–6909 (2,968 frames, 98.93 s).
All missed positions are finite and recovery-eligible; 0.3 supplies no candidate
support there. This is a substantial missed episode, not only boundary imprecision.
Do not treat prior low error rates as evidence for reliable unattended durations.

FRESH_16 latest righting endpoint is 6346 (formerly 6358), with VAF noting a
multi-frame transition. Preserve the 12-frame annotation conflict and both exports.
Frozen 0.4 remains flagged through 6375 (29 extra frames). No detector refit.
Evidence root: `ba_focused_boundary_results_20261012` locally under `outputs/`
and on Firebird under `idtracker_pipeline_runs/`. The 121-run QC dashboard stays
frozen at its pre-import index to preserve active manual exports; current behavioral
interpretation is in the new report and separate review-update record. Investigate
missing candidate support and visual posture; do not solve this by blindly extending
backward search to the human label. Flailing and unseen footage remain unassessed.

### BA Firebird census (2026-10-12)

Read `reports/BA_FIREBIRD_CENSUS_2026-10-12.md` before expanding BA processing.
Read-only lab/home census found 1,229 single-animal TOML copies, grouped into
323 configuration groups (not independent trials). Main BA collection accounts
for 299: 221 have compatible readable tracking, including 121 with confirmed
analysis records/frame outputs and 100 further analysis candidates. Reconcile
versions/rotated videos before counting trials. Forty-four source configurations
have unspecified starts (41 readable trajectories, three absent); 18 have nearby
but nonidentical arena matches; one has different segmentation settings; 15
configurations (14 filenames) lack a matching/nearby session. Outside the main
folder: 20 segmentation drafts, three old input snapshots, one test fixture;
no separate recording collection identified. Scope excludes archives, other
labs/users, software/cache directories and node-local storage. Do not infer
never-processed status solely from absent recognized completion records.

Existing 121-run QC has 36 runs with missing coordinates; 23 lose <=10 frames.
BA004 loses 2,517/7,200 positions (34.96%) over 497 gaps and needs focused
segmentation/footage review. Missing positions are not missing video images or
negative posture labels. Evidence: `ba_firebird_census_20261012` locally under
`outputs/` and on Firebird under `idtracker_pipeline_runs/`. No new tracking
batch or detector change was made; the active manual-review index is unchanged.

### Close-encounter follow-up (2026-10-12)

VAF specified center-to-center entry within one body length and requested who
initiates/leaves close encounters or PSCs. Separate local pilot
`close_encounter_pilot.py` 0.2.0-development and `close_encounter_review.html`
produce `outputs/close_encounter_pilot_20261012/review_set/START_HERE.html`
(port 8777; parent folder has an on-demand launcher). See
`reports/CLOSE_ENCOUNTER_PILOT_2026-10-12.html`. Original orientation pilot remains.
Body lengths are provisional median silhouette-axis extents, not anatomical
calibration. Entry <=1 pair-mean body length or existing inferred PSC; exit
confirmed >1.2 lengths for 0.20 s. First local mover, entry contributor and
leaver are distinct, conservative hypotheses. Unknown tracking without PSC
censors boundaries; inferred positions never supply individual velocity.
102 candidate intervals yield 9 entry and 12 exit estimates and 6 first-local-
mover labels; none of the latter are dyadic. These are UNREVIEWED, not validated
biological counts. Eight focused tests and frozen source/video hash checks pass.
No production rules, prior outputs, Firebird release, or identity-editor work changed.

### 60-pixel encounter revision (2026-10-12)

VAF superseded body-length proximity with 60 original-image pixels center to
center. Separate `proximity60_pilot.py` / `proximity60_review.html` version
0.3.0-development yields `outputs/proximity60_pilot_20261012/review_set/`
(port 8778; parent launcher). Read `reports/PROXIMITY60_PILOT_2026-10-12.html`.
Entry <=60; exit >60 for 0.20s, timestamped at first outside frame. Existing PSC
may maintain inferred contact but PSC-only onset cannot establish a measured
crossing/initiator. Labels are ID/both/unknown for local entry contribution and
exit contribution; first local movement onset is separate. Overlap gaps do not
supply individual motion. 126 candidates, 30 entry and 25 exit attributions are
UNREVIEWED hypotheses. Five focused tests and four source/video hash checks pass.
Earlier pilots and production science remain unchanged; this is local only.

### BA visual disturbance review and exact exclusions (2026-10-12)

Read `reports/BA_VISUAL_PATTERNS_2026-10-12.md`. Ten portable video/trace examples
(four minutes) are in `outputs/ba_visual_patterns_20261012/START_HERE.html` and the
same-named Firebird evidence folder. Review schema is `ba-visual-pattern-review-v2`.
Vince superseded the later-start proposal: exclude ONLY explicitly marked bad
frames, retaining usable footage before and after and the original 7,200-frame
window. Inclusive human ranges become half-open IDtracker intervals. Source
TOMLs remain immutable. `ba_tracking_exclusions.py` prepares attributed plans;
four focused tests pass. No real exclusions or IDtracker reruns were submitted.
Installed IDtracker interval planning supports gaps; production BA postprocessing
still requires adaptation before processing such reruns. Excluded observations
must stay unknown, separately counted, with no inferred motion across gaps.

### BA light-blip tracking rerun (2026-10-12)

VAF explicitly selected original frames 1608–1609 inclusive for exclusion from
Camera_1_40169154_20260627_1614_ACT2.mp4 and requested all 20 TOMLs rerun.
Read `reports/BA_LIGHT_EXCLUSION_2026-10-12.md`. New Firebird/local evidence root:
`ba_light_exclusion_1608_1609_20261012`; Slurm array 918316. Original TOMLs remain
unchanged; C5 retains its original start 10 (others 1095), flagged for review.
Inspect live `BATCH_STATUS.json` and per-cell status before claiming completion.
Original 7200-frame windows have 7198 eligible frames; excluded frames are unknown
and distinct from accidental missing tracking. Production gap-aware BA
postprocessing remains unfinished; no revised behavior/PDF/video release yet.
The BA IDtracker notebook tab records this exact intervention and broader scope.

### Shared video and raw-tracking QC (2026-10-12)

`unified_qc.py` 0.1.0-development is wired into new BA and common dyadic/six-beetle
pipeline runs, plus shared Firebird GUI deployment. Read `UNIFIED_QC_README.md`
and `reports/UNIFIED_QC_2026-10-12.md`. Source checks decode every frame at 160x90
and use content/version/threshold-bound caches. Reports preserve global frame
pairs, scope, raw tracking evidence, and UNREVIEWED status. Skipped/failed scans
are NOT_ASSESSED/FAILED, never clean. Automatic flags cannot exclude or approve.
The 266-test suite and 11 focused checks pass; encoded two-frame flash detection
passes. Actual lighting recording scan: development job 918336, evidence root
`unified_qc_development_20261012`; inspect live results. No biological validation,
old-release regeneration, PSC/turtling rule changes, or complete gap-aware BA
science integration. Legacy standalone and frozen snapshots are not auto-upgraded.

Lighting rerun follow-up: all 20 outputs independently verified in
`ba_light_exclusion_1608_1609_20261012/OUTPUT_VALIDATION_v2.json`, despite IDtracker
exit 1 after Success. Keep exit warnings and initial audit; do not rerun solely
because BATCH_STATUS.json is historical failure. Exact excluded frames are NaN.
Unexpected missingness remains high in D1 (48.53%) and C5 (8.14%); no science
release. Visual-pattern reviewer frame stepping now uses a paused frame index
and midpoint seeking; case hash/scoring schema unchanged, browser fix needs reload.

Shared-QC source scan 918336 completed all 9000 frames. It did NOT flag VAF's
1608–1609 blip; broad lighting candidates 759/767/769/781/2136 and motion
1087/1091/1093 are hypotheses (most before usual start). Preserve discrepancy;
recheck visual/frame reference after the stepping fix, do not alter human
exclusions automatically. Read the updated unified-QC report before promotion.

### D4 image-supported recovery feasibility (2026-10-12)

VAF reports that the real D4 beetle continues its path during spurious jumps and
suspects human shadows. Separate evidence under
`outputs/ba_d4_shadow_feasibility_20261012/START_HERE.html` compares four short
image-template probes against raw tracking. Manually selected anchors and resized
lossy review footage make this feasibility evidence only, not a correction release.
Saved blobs at sampled frames 1754, 1804, 1942, 2133, 2135 include both the visible
beetle and a spurious blob labeled identity 1; frame 1755 has only a large merged
blob. Area alone cannot distinguish all errors. Production trajectories, PSC,
TOMLs and turtling rules are unchanged. Next work should test full-resolution,
uniquely supported candidate recovery with unknown states and held-out controls.
The expanded visual reviewer is `ba_visual_patterns_extended_20261012` locally
and on Firebird; first D4 case spans 648–2300 (1653 encoded frames). Earlier
scores keep their original scope; expanded D4 requires fresh review. The original
review set remains preserved.

### Full D4 recovery comparison ready (2026-10-12)

Authorized D4-only experiment `ba_d4_recovery_review_20261012` is
COMPLETE_UNREVIEWED locally under outputs/ and on Firebird under
idtracker_pipeline_runs/. Job 918347 processed original frames 1095–8294 at
full crop resolution. Original raw coordinates match the frozen fresh_04 array.
Separate proposals retain 6967 frames, change 88 (44 saved-blob selections and
44 image estimates), and leave 145 unknown. Of the 88 proposals, 54 replace
existing coordinates and 34 fill missing positions. No production correction,
TOML, original trajectory, or turtling result changed. Receipt hashes and the
7200-frame encoded video were verified; five algorithm tests and viewer control,
scoring-scope and displayed-frame callback checks passed. Eight representative
image overlays were inspected; browser playback itself was not tool-tested.

Portable viewer: Downloads/BA_D4_recovery_review_20261012/START_HERE.html.
Twenty scenes contain 50.3 seconds at 1x; default playback is 0.5x. Original and
proposed panels share one decoded video. Scope-preserving review export is
`ba-d4-recovery-review-v1`, expected filename
`BA_D4_recovery_review_scores_20261012.json`. Visibility decisions assess unknown
frames only; they do not approve proposed corrections in mixed scenes. Do not
count unseen or unreviewed footage as approved. Initial unknown frames and a long
late gap remain explicit. Rules use provisional area/appearance/movement gates,
ten-frame stable anchors, bidirectional agreement, and a 15-frame image-only
limit. This is a development test, not biological validation or a general-purpose
correction release. Compare the original archived tracking, not the separate
1608–1609 exclusion rerun, when interpreting this viewer.

### Frozen D4 rules tested on five additional cells (2026-10-12)

At VAF's request, array 918350 applied the unchanged D4 recovery functions and
thresholds to ba_092/B3 (same recording as D4), ba_065/B1 (different recording),
ba_004/C2 (severe missing tracking), ba_015/C4 (circling/posture case), and
ba_001/A2 (cleaner comparison). Four recordings, 36,000 frames total. All five
are COMPLETE_UNREVIEWED under `ba_recovery_transfer_20261012` locally and on
Firebird. Portable report and viewers: Downloads/BA_recovery_transfer_20261012/START_HERE.html.

This transfer test is NOT a general correction success. All 140 original >100px
steps disappear from proposed paths, but 106 have an unknown endpoint; only 34
retain proposed positions at both ends. There are 137 proposed replacements and
362 missing-position estimates, alongside 3324 previously available positions
left unresolved. Original missing count 2655 becomes 5617 proposed unknowns.
The cleaner ba_001 has three proposed replacements and 72 unknowns despite no
original missing frames or >100px jumps. Spot checks show useful-looking repairs
and visible beetles in some rejected frames. Do not promote these thresholds or
interpret smoother paths as validated recovery. Original data/scientific outputs
are unchanged. Next development should address overly broad rejection while
retaining explicit uncertainty and test reviewed, targeted repairs.

Five full-video counts/hashes and frozen raw arrays passed; five algorithm tests,
all five actual viewer-script checks, three independent excerpt-alignment checks,
and 15 visual frame inspections completed. Browser playback was not tool-tested.
`VALIDATION.json`, `RULE_PARITY.json`, `SUMMARY.json`, per-run receipts, and the
frozen `REVIEW_CONTROL_PLAN.json` preserve evidence. Each viewer appends two
300-frame comparison windows selected before inspecting results. Schema is
`ba-recovery-transfer-review-v1`; filenames identify each run. Control decisions
cover only shown positions; visibility decisions for unknowns do not approve
other corrections. No unreviewed or unseen footage becomes approved implicitly.

### VAF feedback: major errors only (2026-10-12)

Five transfer-review exports imported into `ba_recovery_feedback_20261012`.
All run identities, hashes and scene bounds verified. 63/98 saved decisions,
31 notes; 35 scenes unscored. Actual shipped/exported schema is
`ba-ba-transfer-review-v1` (duplicated prefix), not the intended name recorded
above. Import recognizes it with strict run/hash/scope checks and preserves raw
exports. Three accept selections also contain cautionary notes; retain both
scopes, do not infer unqualified approval. BA_065 has 15 saved scenes (4–18),
while VAF's verbal report mentioned watching the first 18; do not invent labels.

VAF explicitly rejects broad application: outside the first video, originals
were usually correct or close enough and proposals often lost the beetle.
Latest user constraint: only repair MAJOR errors. Preserve available original
coordinates by default; weak recovery confidence may flag review but must not
remove an available position. Minor centroid differences are not correction
targets. Future proposals require evidence that the ORIGINAL is substantially
wrong plus strong support for a replacement. Source tracking remains immutable.
This feedback import does not change algorithms, apply corrections, or estimate
frame-level accuracy. Read the human-focused START_HERE.html and IMPORT.json
in the feedback evidence root before further recovery development.

### Major-jump-only BA repair pilot (2026-10-12)

VAF's D4 scores support targeted repairs, not the earlier broad recovery behavior.
Read `reports/BA_MAJOR_JUMP_RECOVERY_2026-10-12.md`. Separate
`ba_major_jump_recovery.py` 0.2.0-major-jumps-development starts from exact raw
coordinates and only substitutes image-supported patches touching >100 px jumps,
with >=50 px replacement displacement and <=30 px steps through both observed
flanks. Missing stays missing; weak recovery never removes available positions.
No production processing, IDtracker, source TOMLs or scientific outputs changed.

New evidence root `ba_major_jump_recovery_20261012` contains D4 plus five previous
comparison cells and an additional BA_071/C4 cell from the D4 recording (job
918398). Original >100 px steps to proposed: D4 34→5, BA_092 120→92, BA_065 16→14,
BA_015 4→0, BA_071 14→6; BA_004/001 remain 0 with no replacements. Every original
missingness mask is unchanged. These are development engineering results, not
human-verified correction success rates. Unrepaired jumps remain explicitly
flagged, not automatically censored. BA_071 is a new cell, not a new recording.

The D4 score export is preserved with source hash and scoped decisions. Fourteen
accept, five visibility-only, one reject; the rejected 3785–3791 scene is unchanged.
New viewer schema `ba-major-jump-review-v2` shows trails and full-run plots by
default. Four BA_071 scenes include repaired and unrepaired jumps. Seven gate
tests and all seven viewer-script checks pass; reused media hashes/encoded counts
are checked. Static overlay samples were inspected; browser playback is not
established by script tests. All proposals remain COMPLETE_UNREVIEWED.

### Major-jump review feedback received (2026-10-12)

Eight score exports for seven runs imported into
`outputs/ba_major_jump_feedback_20261012/`. Both BA_071 exports have identical
substantive decisions; preserve both and count once. Strict schema, data hash,
source, frame and decision-scope checks passed. Twenty of 26 scenes have saved
decisions; six remain unscored. Twelve correction scenes accepted, two rejected;
three original-tracking checks accepted, one rejected; two visibility-only labels.
Do not interpret blank scenes as negatives or visibility as tracking approval.

Both BA_071 repair scenes accepted; the other two scenes remain unscored. D4's
rejected scene includes VAF's note “Frame 2007-2011 are wrong.” All five positions
were retained original coordinates, identifying an unresolved error rather than
proof of newly introduced errors. BA_092 rejects the retained-track scene at
1418–1571 and the correction scene at 1673–1789 with residual-major-jump feedback.
The latter contains 15 substitutions, but the note does not adjudicate each one.
Keep both rejected correction scenes unresolved, not automatically approved by
this interpretation. Next development should study complete erroneous excursions
and observed return evidence while retaining accepted/clean regression cases.
No rule changes, scientific correction application or population accuracy claims
followed this import. Human-focused report: feedback root `START_HERE.html`.

### BA excursion repair follow-up (2026-10-12)

At VAF's request, separate `ba_excursion_recovery.py` 0.3.0-excursion-development
extends supported major-error segments to include smaller lead-ins and adds
short directional recovery candidates only with continuity and two-flank image
checks. See `reports/BA_EXCURSION_RECOVERY_2026-10-12.md`. Frozen previous
replacements and every missingness mask stay exact. No production changes or
IDtracker runs. Large steps after previous→new: D4 5→3, BA_092 92→2,
BA_065 14→10, BA_071 6→0; other three runs unchanged. These are engineering
counts, not verified error reductions. Directional evidence is original recovery
output, with additional appearance checks on compressed full-resolution crops.

Evidence root `ba_excursion_recovery_20261012` contains nine short review clips,
855 frames total, and seven full-run result arrays/audits. Traces are displayed
by default; `ba-excursion-review-v1` stores trace and video judgments separately.
Trace approval is never position validation. Video approval covers new replacements
only; notes-only/blank scenes remain unscored. D4 2008–2011 is newly repaired;
2007 remains unchanged and displayed for VAF to adjudicate. Static overlays,
encoded counts, 27 alignment comparisons, regression and viewer-script tests
passed. All outputs remain UNREVIEWED pending returned scores.

### BA excursion scores received (2026-10-12 local)

VAF's `BA_excursion_review_scores_20261012.json` imported with strict result-hash,
scene and scope checks into `outputs/ba_excursion_feedback_20261012/`. All nine
scenes have video and trace decisions: five repair accepts, three repair rejects,
one accepted unchanged control; six plausible traces and three flagged traces.
D4's target error stretch and both BA_092 target stretches accepted for NEW
replacements only. Early scenes rejected: D4/BA_092 1095–1139 and BA_065
1373–1470. BA_071's same starting window accepted; do not infer a universal
initial-frame exclusion rule. Shared source/time in D4/BA_092 suggests investigating
shared disturbance, not proof of cause. BA_071 1725–1785 accepted with residual
stationary-jitter note. Preserve that qualification and all raw scores. No rule
changes or scientific correction application followed the import. Report at the
feedback root `START_HERE.html`. Score timestamps are October 13 UTC, October 12
America/New_York; use the local date for this checkpoint.

### BA starting-scene investigation (2026-10-12)

Read `reports/BA_STARTING_SCENE_REACQUISITION_2026-10-12.md`. Separate
`ba_stationary_reacquisition.py` 0.4.0 development addresses only four selected
short stationary scenes. It proposes 4 D4, 3 BA_092 and 14 BA_065 image-based
replacements. BA_065 also proposes missing values at 1442–1443 and 1447–1448,
where image evidence fails during hand/sleeve coverage. Original coordinates
remain available. This is explicitly a provisional missing-value proposal,
not permission to drop positions whenever a tracker lacks confidence.

BA_071's accepted starting scene is unchanged, and accepted scenes in the four
full arrays remain exact. Other runs/production outputs untouched. The viewer
in `ba_starting_recovery_20261012` contains four clips, 233 encoded frames, with
traces and explicit missing-frame labels. Schema `ba-starting-review-v1` separates
trace judgments from video decisions; video approval covers new replacements
and proposed missing observations only. Five tests, accepted-scene checks,
12 alignment checks and viewer-script tests passed. Await VAF review; no broad
stationary-reacquisition or disturbance rule has been validated.

### Starting-scene review accepted (2026-10-12 local)

`ba_starting_feedback_20261012` preserves VAF's returned export with verified
schema, result hash, scene bounds and scopes. All four video accepts and four
plausible traces: 21 new positions and BA_065 missing observations 1442–1443,
1447–1448 accepted within the shown scenes. Crucial BA_071 note: “The proposed
is good the orignial is not.” The control is unchanged relative to the previous
PROPOSAL, not original tracking; do not interpret its generic exported control
scope as approval of raw IDtracker positions. Original export is unchanged;
normalized import explicitly records the interpretation. No broad release,
scientific coordinate mutation or population accuracy follows. Next milestone
is frozen-rule transfer testing on unused jump-heavy cells/recordings with clean
controls; stationary recovery still requires eligibility checks and validation.

### Frozen BA transfer test ready (2026-10-12)

Authorized eight-cell recovery transfer test COMPLETE_UNREVIEWED. Read
`reports/BA_FROZEN_TRANSFER_2026-10-12.md`. Evidence root:
`ba_frozen_transfer_20261012` locally and on Firebird. Five jump cases
BA_082/059/032/014/067 and three clean controls BA_058/016/051 were fixed before
results; five recordings, three new to correction development (not necessarily
unseen in prior BA/turtling work). Candidate/0.2/0.3/0.4 functions and thresholds
were frozen and hashed. A new predeclared stationary-window eligibility policy
is being tested; do not treat it as previously validated automatic eligibility.

All 57,600 observations processed from existing tracking; no new IDtracker jobs.
Twenty-three proposed replacements reduce >100 px steps 26→1, with no added
missing observations. All three clean controls remain exactly unchanged across
full runs. BA_059 retains one large step. No biological accuracy estimate or
approval follows. Arrays, audits, frozen hashes, full remote crop videos, frame
counts, source/media checks and 33 clip-alignment comparisons verified. Eight
static overlay pairs inspected, viewer scripts pass; browser playback not tested.

Downloads `BA_frozen_transfer_20261012/START_HERE.html`: 11 clips, 816 encoded
frames, 27.2 seconds at 1x. Traces visible by default, video/trace scoring separate.
Expected `BA_frozen_transfer_scores_20261012.json`, schema
`ba-frozen-transfer-review-v1`. Await attributed scores. Array 918542 and packager
918553 complete. Source tracking/TOMLs/scientific outputs remain unchanged.

### BA frozen transfer feedback (2026-10-12)

VAF returned all 11 frozen-transfer decisions. Seven of eight repair scenes and
all three controls accepted; nine traces plausible, two flagged. BA059 frames
1095–1139 have a rejected repair and flagged trace. BA082 1095–1139 has accepted
repairs but a flagged trace. Both concerns remain unresolved; do not treat this
as an all-pass result or infer frame-level accuracy from scene decisions.
BA058's “Turtled” note is qualitative, without exact posture endpoints.
Original export and scope-checked decisions are preserved in
`outputs/ba_frozen_transfer_feedback_20261012/`, with the same-named Firebird
folder under `idtracker_pipeline_runs/`. `START_HERE.html` summarizes findings.
A larger frozen-rule proposal/review batch is recommended; none was launched by
this import. Raw tracking, scientific outputs and correction rules are unchanged.

### Additional 100-cell BA recovery batch (2026-10-12; running)

VAF authorized 100 additional cells with originals preserved and a viewer ranked
by jumps/QC, traces visible by default. Read
`reports/BA_ADDITIONAL100_RECOVERY_2026-10-12.md`. All 100 selected census cells
across 14 recordings passed live input checks; two stale registry choices were
resolved to exact-settings archived sessions before execution. Source TOMLs,
videos and tracking remain immutable. Frozen recovery modules are unchanged;
18 focused tests pass. Array 918599 runs recovery and per-cell review packaging;
index job 918616 follows after any array outcome and lists incomplete cells.
Local/Firebird root `ba_additional100_recovery_20261012` under `outputs/` and
`idtracker_pipeline_runs/`. Treat outputs as UNREVIEWED. Verify live receipts,
media, hashes and download before claiming delivery. No production or turtling
rule changes; starting-window repairs explicitly retain high review priority.

Additional100 provenance update: 11 selected cells from Camera1 1614_ACT2 now use
the verified VAF light-exclusion reruns, preserving older attempts under
`superseded_original_tracking_attempts/`. Replacement array 918694; index 918616
now depends on both arrays, validation 918650 follows. Separate exclusion adapter
resets candidate state and splits stationary evidence at 1608–1609; thresholds
unchanged. Missing percentages for these cells use 7198 eligible observations;
intentional exclusions are labeled separately. Do not revert to initial census
session choices or combine their counts with current rerun-baseline results.

Additional100 completion: all 100 are COMPLETE_UNREVIEWED. Final baselines:
723 >100px steps; proposals: 230; 1046 replacement positions in 26 cells;
74 full arrays unchanged, no added missing. Existing 22 deliberate exclusions
remain separate. 398 short scenes / 50461 frames / 28.03 minutes at 1x; all100
full-run views preserved. 1194 clip alignment checks and 42 source checks across
14 recordings pass; 1896 downloaded hashes and 200 viewer logic checks pass.
Downloads `BA_additional100_recovery_20261012/START_HERE.html` is the full ranked
viewer. Local output-root START_HERE is a launcher to that collection. New015
retains 192 jumps; AI spot check flags new041 frame933 as potentially misplaced.
Neither jump reduction nor artifact checks establish biological accuracy. Read
final report and receipts before downstream use. Browser playback not tool-tested.

### BA additional100 viewer navigation fix (2026-10-13)

Full-run pages contain one scene, so old Next/Previous silently stayed in place.
Navigation v2 installed in all 300 Downloads scene/full/portable pages: scene
buttons advance within a run, then cross to adjacent runs in fixed QC order;
full-run buttons move directly between runs. End-of-collection returns to index.
Final-scene video decisions save before advancing. Draft notes are retained.
Embedded review data, score schema/hash and storage keys are unchanged.
All 300 navigation tests pass. Prior HTML is in Downloads navigation_v1_backup;
NAVIGATION_RECEIPT_v2.json records old/new hashes. Original HASHES.json files are
historical v1 records; use the navigation receipt for updated HTML hashes.
Evidence and deployable pages: outputs/ba_navigation_fix_20261013. No tracking,
media, scientific data or human score files changed. Reload open pages to apply.

### Combined BA100 score export (2026-10-13)

Downloads BA_additional100_recovery_20261012/ALL_SCORES.html now provides a
user-operated Collect saved scores button, one combined JSON download, and
per-run marks/coverage counts. All 300 review pages have an export relay and
collector link. It reads each page's unchanged localStorage key only when the
user starts collection; no marks are removed. Full-run versus scene scopes and
source-page versions remain separate. Combined schema:
`ba-additional100-combined-review-v1`. Records retain original nested attributed
`ba-additional100-review-v1` payloads, imports and history. Deduplicate identical
scope copies and preserve conflicts when importing; never count blank/unreadable
pages as negative labels or assume a watched page was scored.

Important: browser access to file URLs was security-blocked. Codex did NOT read,
recover or back up the user's browser marks. User must collect and download in
the same browser. Collection failures and incomplete coverage are visible.
Code-only installation receipt COMBINED_EXPORT_RECEIPT.json explicitly records
this distinction. Earlier HTML preserved in combined_export_predecessor.
Evidence: outputs/ba_combined_scores_20261013. Synthetic collection/hash/scope
checks and all 300 navigation regressions pass; real saved-score collection is
unverified pending user action. No scientific/media/data or storage keys changed.

### BA100 returned scores and remaining queue (2026-10-13)

Eight uploaded exports are preserved byte-for-byte in
`outputs/ba_additional100_feedback_20261013/original_scores/`. Strict dataset-hash,
scene-bound and label validation passed. Repeated new_020/new_021 exports contain
identical decisions; four distinct scopes contain 42 video decisions (23 accept,
14 reject, five unsure). new_016 has six, new_020 ten, new_021 25 of 32 scenes;
new_041 has a rejected full-run decision. Its nine scenes count as watched via
full-run coverage, not individual scene approvals. User notes remain verbatim.
No tracking, start frame, exclusion or correction rule was changed.

Downloads BA_additional100_recovery_20261012/START_HERE.html and REMAINING.html
now show the uploaded-score checkpoint: 348 remaining scenes across 97 runs,
in existing QC order. new_021 resumes at scene26. ALL_RUNS.html retains the
complete index. All300 pages seed only absent decisions from validated uploads;
existing browser decisions win, and uploaded originals remain separately saved.
#remaining navigation skips locally scored scenes. Reject/unsure mean watched
with unresolved issues, not approved. Static index counts are the import
checkpoint, not live browser totals. ALL_SCORES includes uploads and can collect
additional marks via user action; IMPORTED_ALL_SCORES.json is a combined backup.
Browser-only marks were not read by Codex. 300 synthetic page checks passed;
305 installed file hashes verified. Playback was not browser-tested. Prior HTML
is in feedback_import_predecessor_20261013. Evidence, scripts and receipts are in
outputs/ba_additional100_feedback_20261013. No broad scientific approval follows.

### BA gap-recovery pilot and combined feedback (2026-10-13)

Five combined score exports are preserved in
outputs/ba_additional100_combined_feedback_20261013: 160 distinct decisions across
14 runs (155 short scenes, five full runs; 74 accept, 81 reject, five unsure),
no conflicting copies. Latest four exports report all300 pages collected; this
is collection completeness, not review completeness or population accuracy.

User authorized a bounded missing-gap experiment and suggested 45–60px endpoint
distance. Read reports/BA_GAP_RECOVERY_PILOT_2026-10-13.html. Separate
ba_gap_recovery_experiment.py 0.1.0 retains existing finite coordinates and human
exclusions. Short interpolation: <=15 missing frames, five-frame flanks, <=4px
average implied step, ROI containment. Frozen25px trial allows161 interpolated
positions across six runs; sensitivity45/60 both allow180. Image matching on
16–300-frame gaps requires two fixed flank templates and bidirectional support;
33 image candidates pass. CANDIDATE_45.npz combines180 interpolated +33 image
positions; PROPOSAL.npz retains25px trial. No production defaults/TOMLs changed.
Review videos are spatially full-resolution but lossy crops, not source reruns.
Long/unbounded gaps remain missing. Template matches are image estimates, not
segmentation observations. Never use interpolation as posture evidence.

38 masked reference-track gaps within accepted clips:36 reconstructed at every
threshold, maximum difference6.25px. Acceptance does not validate every retained
coordinate; this is not independent biological validation. Eight focused tests
pass. Eight viewer clips contain1135 frames (37.83sec), encoded counts and24
alignment checks pass; JS frame/notes/export checks pass. Still examples inspected;
browser playback not tested. Downloads/BA_gap_recovery_pilot_20261013/START_HERE.html
has traces by default and single export BA_gap_recovery_scores_20261013.json.
Evidence: outputs/ba_gap_recovery_pilot_20261013, including hashes/receipts.
Distance sensitivity is <0.56% relative to adjacent-finite sums, which omit long
missing intervals; do not infer that scientific conclusions are stable from this.

### Full new_072 interpolation review (2026-10-13)

VAF identified frames4141–4153 in the gap pilot and requested a gap-heavy full-run
viewer showing every interpolation. Actual missing subranges4142–4150 and4152
are separated by retained observations; endpoints33.42px/7.34px apart. Separate
outputs/ba_gap_fullrun_new072_20261013/build.py tests relaxed flank support: nearest
additional finite point within15 frames on each side, <=45px displacement and
<=15px/frame, replacing five consecutive flank frames. Gap <=15 frames, endpoint
<=45px, mean <=4px/frame, ROI/protected exclusion guards remain. Do not generalize
this relaxed experiment to production. 108 gaps/413 frames proposed; 3515 remain
missing; no existing finite position changes. This trial is interpolation-only,
without earlier image candidates. Original25/45px pilot outputs remain untouched.
Downloads/BA_new072_all_interpolations_20261013/START_HERE.html shows full7200-frame
video, orange interpolation markers, traces by default, gap navigation and a
button for VAF's reported gap. Per-gap scoring is optional; one combined export
BA_new072_all_interpolation_scores_20261013.json uses ba-all-interpolation-review-v1.
Counts, protected inputs, actual7200-frame decode and JS controls/export checked;
browser playback not tested. Evidence/receipt local; no Firebird upload asserted.

### new_072 interpolation one-second trial (2026-10-13)

VAF suggested gap331–347. It has17 missing frames and38.5px endpoint separation;
the half-second duration cap alone rejected it. Separate experiment
outputs/ba_gap_fullrun_new072_v2_20261013 uses <=30 missing frames, retaining
45px endpoints,4px/frame mean, relaxed measured flank support and ROI/exclusion
guards. 116 candidate gaps/566 inferred frames; eight gaps/153 frames added;
3362 remain missing. Existing measurements and all108 previous proposals remain
unchanged. No automatic production adoption or posture inference. Eight additions:
331–347,631–646,1914–1933,2167–2186,2773–2789,5897–5923,6482–6499,6582–6599.
Downloads/BA_new072_all_interpolations_v2_20261013/START_HERE.html opens at331 and
has Next newly added gap. Prior viewer/scores retained. Combined export filename
BA_new072_all_interpolation_v2_scores_20261013.json uses a new dataset hash.
Array invariants, source-video identity, viewer logic and delivery hashes checked;
browser playback not tested. Local evidence only; no Firebird upload asserted.

### new_072 more permissive interpolation v3 (2026-10-13)

VAF explicitly requested greater permissiveness while retaining interpolation
provenance, citing endpoints1504–1511,1625–1628,1628–1631. Missing subranges are
1505–1510,1626–1627,1629–1630. First endpoint separation55.31px; latter gaps
~40px in3frame steps exceed old4px/frame gate. Separate local experiment
outputs/ba_gap_fullrun_new072_v3_20261013 tests <=30 missing frames, <=60px
endpoints, <=20px/frame mean, measured support within15frames on each flank
with <=60px separation/<=25px/frame, ROI and exclusion guards.504 gaps/1503
positions proposed,2425 missing retained.388gaps/937frames added versusv2.
This is a user-directed exploratory relaxation, not independently validated.
Finite coordinates and prior proposals unchanged. No production adoption.
Downloads/BA_new072_all_interpolations_v3_20261013/START_HERE.html has direct
buttons for all3examples, Next newly added gap, orange inferred markers,
traces and optional scoring. INTERPOLATION_FRAMES.csv has7200 rows preserving
baseline/candidate positions, status, endpoint frames, gap id and new-in-v3.
Original media matches earlier checked7200frame video; array invariants,
CSV scope, JS navigation/export and delivered hashes pass. Browser playback
not tested. Export BA_new072_all_interpolation_v3_scores_20261013.json has
new dataset hash; earlier viewers/scores preserved. Local evidence only.

### Frozen interpolation transfer, four recordings (2026-10-13)

VAF accepted the direction/settings of new_072 v3 without reviewing all gaps and
requested application to a few more videos, with full-run viewing and overall
verdicts. Separate outputs/ba_interpolation_transfer4_20261013 freezes the exact
v3 decision block (frozen_rules.py) and verifies bitwise/equal-NaN replay of the
new_072 proposal and method labels. No retuning on transfer runs. new_093 adds
304 inferred frames/73gaps; new_021286/50; new_0789/5. Each comes from a different
source recording. Fourth recording new_088 is an unchanged zero-gap control.
Original finite coordinates and human exclusions retained. Substantial long
missingness remains (5062/3207/34/0unexpected frames respectively). No posture
inference, broad production adoption, or blanket human approval implied.
Downloads/BA_interpolation_transfer4_20261013/START_HERE.html has three4min test
runs +optional4min control,1x/2x/4x, traces/orange markers, optional gap navigation,
one verdict per full run, and combined BA_interpolation_transfer4_scores_20261013.json
(schema ba-interpolation-transfer-fullrun-v1). SUMMARY.html links per-frame CSVs
with raw/baseline/candidate positions and endpoint provenance. Every video decoded
7200frames; media hashes,28800CSV rows, coordinate invariants and JS save/navigation
checks pass. Representative trace inspected; browser playback not tested. Earlier
viewers/scores preserved. This targeted selection is not population accuracy.
Evidence/receipts local; no Firebird upload asserted.

### BA-only interpolation boundary and speed-based trial (2026-10-13)

VAF explicitly restricts ALL interpolation development here to BA single-animal
videos. Never apply these gap-fill rules to dyadic or multi-animal/group data.
This restriction does not change the separate turtling work. Existing scientific
inputs stay immutable and interpolated positions must remain separately labeled.

New local outputs/ba_interpolation_speed_transfer4_20261013 removes fixed total
distance caps at VAF's request; retains <=30missing frames, <=20px/frame implied
movement, nearby measured support <=25px/frame, ROI/exclusion checks. Its
frozen_rules.py requires explicit collection='BA' and integer number_of_animals=1,
rejects unknown/multiple/nonBA scopes and wrong array shapes. Build verifies source
TOML hashes/counts against saved Firebird census before calling. Seven invalid-scope
tests pass. Earlier scripts are historical snapshots, not production entrypoints.
new_093 adds10gaps/115positions versus prior transfer (83gaps/419inferred total);
other runs unchanged (new_021286frames, new_0789, new_0880). All prior finite
positions/proposals and exclusions unchanged.28800decoded video frames and CSV
rows checked; JS controls checked; browser playback not tested. No group/dyadic,
turtling code or production routes changed. New viewer and frame provenance:
Downloads/BA_interpolation_speed_transfer4_20261013/START_HERE.html. Single export
BA_interpolation_speed_transfer4_scores_20261013.json uses new dataset hash.
Local evidence only; no Firebird upload asserted. Human review still needed for
newly allowed bridges; no inference of full-run or population accuracy.

### BA speed-based interpolation feedback received (2026-10-13)

VAF said the result looks very good and returned
BA_interpolation_speed_transfer4_scores_20261013.json. Strict schema, dataset
hash, four run IDs/frame scopes and labels verified; source export preserved in
outputs/ba_interpolation_speed_feedback_20261013 with importer/IMPORT_RECEIPT.json.
new_093 and new_078: usable; new_088 unchanged control: usable. new_021: needs_work
without a note. Preserve that explicit exception despite positive overall comment;
do not treat all four runs as approved. These are full-run qualitative verdicts
on interpolation, not per-frame position/posture labels or population accuracy.
No automatic science release, broad batch, threshold change, or turtling change.
Interpolation remains BA one-animal only; downstream human QC still needed for
flagged runs, unresolved long gaps and pre-existing trajectory errors.

### BA interpolation freeze and all-compatible batch (2026-10-13)

VAF authorized all verified compatible BA cells. Read
reports/BA_INTERPOLATION_FREEZE_2026-10-13.md and
reports/BA_COLLABORATOR_REVIEW_2026-10-13.md. BA-only single-animal
ba_interpolation.py 1.0.0 is frozen (commit c20c8be); portable reviewer and
packaging follow in f580cbd/59641a8. Four-transfer exact parity and306 tests pass.
221 configurations from14 recordings are selected in
outputs/ba_frozen_interpolation_all_20261013/PLAN.json, mirrored on Firebird.
Slurm918854 processes existing tracking;918903 hashes recordings;918907 checks
representative alignment;918904 packages only after successful dependencies.
Verify live RELEASE_RECEIPT.json/PACKAGE_RECEIPT.json before claiming completion.
Prior100 recovery proposals are retained as baseline; older121 use compatible
raw tracking. All20 lighting cells use verified reruns with1608–1609 protected.
Do not present this as universal new shadow recovery or biological approval.
Turtling remains NOT_ASSESSED, and separate QC dashboard work is unchanged.
New portable scores are ba-frozen-tracking-qc-v1, bound to dataset hash and
reviewer/coverage. Never silently merge conflicting scores or approve unseen frames.
Original inputs and earlier scores/packages remain immutable.

BA221 completion: RELEASE_RECEIPT.json is COMPLETE_UNREVIEWED for all221 windows.
6,711 interpolated frames/1,910gaps;11,370 unexpected missing;33runs/490remaining
>=100px jumps;40protected exclusions.84 source-alignment samples,1,768local hashes,
all1,591,200CSV rows and221 exact rule replays pass. Downloads/BA_frozen_221_QC/
START_HERE.html and adjacent BA_frozen_221_QC.zip are verified; ZIP SHA-256
712f557e84c717c98ff386aa0305c5ac058bed02a4af7249fc01175afdff84a3.
Read reports/BA_FROZEN221_DELIVERY_2026-10-13.md for the completed handoff.
Notebook BA IDtracker entry/contents link updated and read back. Browser playback
is NOT_TOOL_VERIFIED. Serial alignment918907 passed; parallel919085/919103 were
canceled as redundant after it finished. Interpolation science remains1.0.0;
CODE_FREEZE.json records final reviewer code. No collaborator messages sent.

### Uniform BA recovery/interpolation and fast QC (2026-10-13)

Read `reports/BA_COMBINED221_RESULTS_2026-10-13.txt` and
`reports/BA_COMBINED221_HANDOFF_2026-10-13.txt`. The earlier221 package mixed
100 recovery inputs with121 raw inputs. The replacement applies identical frozen
recovery then BA interpolation1.0.0 to all221, preserving originals. Remote root:
`ba_combined_recovery_221_20261013` under `idtracker_pipeline_runs/`; authoritative
portable artifacts are in `delivery/`. Verify RELEASE_RECEIPT/PACKAGE_RECEIPT.
All100 older additional-cohort arrays replay exactly. Raw983 jumps become306
across12 movement-blocked cells;1,251 recovered and6,715 interpolated positions;
11,370 unexpected missing observations;40 deliberate exclusions preserved.

The new trace-first dashboard uses `ba-combined-qc-v1`, separate storage and
historical review context. Coverage uses radio buttons; IDTracker-rerun checkbox
records a request only. It does not submit jobs. Preserve prior marks and exports.
Strict gate0.1.0 masks unresolved jump endpoints and blocks all movement steps
for affected runs. Use STRICT_ANALYSIS.npz, not the ungated comparison proposal,
for downstream movement. Frozen0.4 posture hints use recovery BEFORE interpolation;
interpolated/missing/excluded/jump-blocked observations stay unassessed. Known
BA030/BA060 misses preclude unattended duration claims. No production PDF/behavior
regeneration,dyadic extension or biological approval follows from this QC package.


### Savannah BA TOML reruns and new QC queue (2026-10-14)

Read reports/BA_SAVANNAH_RERUNS_2026-10-14.txt. Found 12 revised BA TOMLs in
Firebird’s 2026_BA/BA R1 Reruns folder, owned by svonesh1-guest-swat and saved
on October 14. VAF explicitly skipped BA_065 (empty tracking interval);
NEW_093 was not found. Eleven reruns are COMPLETE_UNREVIEWED in
ba_savannah_reruns_20261014 under local outputs/ and Firebird’s
idtracker_pipeline_runs/. Successful tracking 920118, processing 920120,
packaging 920121; initial wrapper failure 920102 is preserved.

New packet: BA_Savannah_reruns11_QC_20261014/START_HERE.html. BEFORE_AFTER.html
shows old/new traces, windows and prior decisions. Existing 221-cell packet
and storage are unchanged. Checks passed for all 11 videos (7,200 frames each),
353 file hashes, exact interpolation replay and 33 source-alignment samples.
NEW_021 retains 21 jumps and 3,088 missing positions and remains movement-blocked;
the other ten have no remaining large jumps or unexpected gaps. BA_070 and
NEW_059 posture candidates are screening hypotheses. Five lighting cells retain
1608–1609 exclusions. C5 now starts at 1096. Source snapshots and derived
submissions are preserved separately.

Registry: 11 explicit rerun links, all 227 old review records preserved, zero
new reviews. Dataset f625af677617324b89e280fa3656fa641aeb0b28ffda4fecb906c51369d83c91.
No old approval transfers. Browser file-URL policy blocked automatic opening;
interactive playback is unverified. The existing BA notebook tab records
completion, exact TOMLs, and the private Drive link to VAF’s original QC export.
No production analysis extraction or Git commit was made. Discussion agenda:
reports/BA_ANALYSIS_DISCUSSION_2026-10-14.txt.

### BA scientific selection checkpoint (2026-10-14)

Read `reports/BA_SCIENTIFIC_DATA_CHECKPOINT_2026-10-14.md` and `provenance/ba_science_selection_20261014/READ_ME.txt`. VAF returned all 11 Savannah rerun decisions: nine approvals; NEW_015 and NEW_021 excluded. Explicit lineage gives 180 approved and 41 excluded selected cells across 14 source recordings. BA_065 was skipped and NEW_093 had no revised TOML; their old exclusions remain. Do not fall back to prior tracking for rejected reruns or count both versions. Four approved cells retain strict movement holds: BA_059, BA_092, NEW_041, NEW_088; no override was supplied. 176 approved cells have no movement hold.

Authoritative selection tables, complete manifests/reviews, original QC exports and source hashes are in `provenance/ba_science_selection_20261014/`. Frozen numerical files and closed registry backups are under `outputs/ba_science_selection_20261014/` and the same-named Firebird archive. Use `STRICT_ANALYSIS.npz` for movement; `FRAMES.csv` is pre-strict interpolation output. Preserve raw/recovered/interpolated/excluded provenance and never bridge unknown gaps. The original packet manifests remain historical COMPLETE_UNREVIEWED; the separate selection binds VAF approvals to their exact hashes.

Vince now requests wall time, fungus time, latency to move and total distance as frame-indexed raw measures: temporal outputs in frames, distance in original-image pixels. Implement a new extractor only after settling the remaining definitions in the report. BA TOMLs have only arena geometry; do not fabricate a fungus ROI or return absent geometry as zero. The older 30-pixel wall/latency settings are documented defaults, not newly adopted scientific definitions. Track approval does not validate automatic turtling duration. Current checkpoint verification: 221 selected manifests and artifacts match; 685 prior input fingerprints match; 14 source videos newly hashed; 143 BA Python tests and 11 JavaScript scripts pass.

## 300-frame fight dashboard screen (2026-10-16)

Vince selected context_300 for the operations fight dashboard. Read reports/DYADIC_LONG300_DASHBOARD_2026-10-16.md. The separate dyadic_turtling_long_bouts.py 0.1.0-long300-qc supplies 105 candidate intervals across 98 current packets; all 34 development masks replay exactly. It remains screening only. BA and shared production defaults are unchanged; six-beetle/editor pauses remain. Full scientific suite: 353 tests passed using the existing local scientific dependencies.
