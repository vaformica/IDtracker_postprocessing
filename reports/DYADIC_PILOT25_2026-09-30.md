# Dyadic development pilot — 30 September 2026

Status: **25/25 complete, technically verified, UNREVIEWED**. Local entry point: `outputs/dyadic_pilot25_20260930/review_set/START_HERE.html`.

Vince authorized a smaller test set after withdrawing the 99-run PSC 1.5.1 outputs. This run uses PSC **1.5.2**, processor **0.8.1-group**, review viewer **v4**, and PDF style **outlined-psc-v1**. It reuses immutable IDtracker trajectories and detection evidence; it does not rerun tracking.

## Selection and inputs

The original eligible population contains 99 cells across 12 recordings. Seed **20260930** selects two cells per recording and one additional cell, for 25 runs. A1 and B2 of `Camera_2_40359705_20260702_1536_FIGHT_ACT2` were deliberately included because both had beetle 0 classified as PSCP at the reported global frame 3005 in the withdrawn release. The other 23 choices use the seed. This is a rule-development sample, not an unbiased behavioral prevalence sample.

Five selected cells retain `PAPER_DATA_WRONG` in their source filenames. They remain visibly flagged; the name alone is not an automatic exclusion rule. Each run uses **7,200 inclusive frames** from its own TOML tracking start, a **60-pixel** social radius, and the shared processor's other existing defaults. Artifact filenames retain the original recording and cell stem.

Firebird output root:

`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_25_run_development_psc_v1_5_2_viewer_v4_20260930`

Authoritative records are `plan.json`, `SELECTION.csv`, `PREFLIGHT.json`, `CODE_SNAPSHOT.json`, `TEST_RECEIPT.json`, per-run manifests/receipts, and the eventual `RELEASE_RECEIPT.json`. Local staging and QA are in ignored `outputs/dyadic_pilot25_20260930/`.

## Execution and checks

`dyadic_pilot25.py` selects, preflights and runs the sample. `dyadic_pilot25_package.py` packages portable review/PDF links and creates separate per-run ZIPs. The original analysis snapshot stays frozen; the packaging successor has its own `PACKAGER_SHA256.txt`.

All 25 input preflights passed. Fifty-six deployed science tests passed. The initial deployment omitted `reviewed_contacts.py`, causing one test-module import failure; the unchanged helper was added, the two affected tests passed, and both logs remain in the record. No algorithm was changed to repair that deployment issue. A local full-suite attempt stalled in the matplotlib/font-cache environment and was terminated; it is not counted as a passing run.

Slurm job 914273 processed the first cell and passed all checks. Array 914275 processes the remaining 24, initially capped at 12 concurrent jobs and later raised to 24 using available compute capacity. Pending tasks were moved from the busy default partition to the available standard compute partition. Packaging job 914308 and visual-check job 914311 depend on all array tasks succeeding.

Each run checks the inclusive frame window, raw/PSC tables, output hashes, source integrity, named HTML/video pairing, both PDF versions, and **both encoded and decoded MP4 frame counts**. The outlined renderer recomputes and matches the canonical states before writing. Packaging requires every run to be complete, tests each ZIP, and records checksums.

The first regular PDF was visually reviewed across all ten pages; a representative outlined page and decoded video frame also rendered correctly. Browser automation rejected a local `file:` URL, so interactive playback was not checked through that browser tool. Static links, video decoding, metadata, and artifact rendering are checked separately. These are technical checks, not biological approval or proof that the reported episode is corrected.

## Review workflow

**The exact reported episode remains unconfirmed:** new PSC 1.5.2 frame tables still classify beetle 0 as `PSCP_BLOB` at global frame 3005 in both A1 and B2 of `Camera_2_40359705_20260702_1536_FIGHT_ACT2`. The continuous beetle-0 `PSCP_BLOB` segment begins at frame 2970 in A1 and 2977 in B2; both identities already share a group before those transitions. This supports inspecting persistence and identity attribution, rather than claiming the entry-gate correction fixed the episode. The review index flags both cases prominently. The pilot remains on the frozen 1.5.2 analysis code for consistent rule-development review.

Visual clarification after inspecting the exact decoded images: at **global frame 3005**, the beetles appear close together in both A1 and B2. Thus the retained PSC classifications do **not**, by themselves, establish that Vince’s reported error persists. Confirm the exact cell and whether frame 3005 refers to the source/global frame or the review-video frame. This supersedes the earlier interpretation that retaining the classification established persistence of the reported error. Neither visual proximity nor these labels proves correct identity attribution.

The completed package exposes `START_HERE.html`, a run index, and a blank attributed review worksheet. Compare raw and PSC positions, record the full recording/cell and global frame, and export decisions separately. Start with A1 and B2 of the reported recording around frame 3005. Unsupported contact, identity uncertainty, and presumed paths still need scientific review before scaling back to the 99-run population.

## Completion and local delivery

All 25 runs completed without analysis/validation failures. Each of the 25 MP4s has 7,200 encoded and decoded frames. All 50 regular/outlined PDFs, raw/PSC CSVs, source integrity checks, and 26 ZIP integrity tests passed. All 25 PDF covers and representative video frames were rendered and visually inspected as contact sheets; named links also passed. This does not constitute frame-by-frame scientific review.

The Firebird full ZIP is `Dyadic_25_run_development_test_PSC1.5.2_viewer4__review_note_v2.zip`, 1,993,800,301 bytes, SHA-256 **95525992d1b4f5c8be35aa7e1dc1f5bc80b39886ada005c9e32436c229955c23**. Individual run ZIPs are in `individual_run_zips/`. `RELEASE_RECEIPT.json` records completion at 2026-09-30 18:58:20 UTC.

The expanded local review set contains 25 HTML/video pairs and 50 PDFs. `LOCAL_VERIFICATION.json` confirms all **775 run-file hashes**, **31 frozen code-file hashes**, all index links, and selection parity; run files total 2,145,691,690 bytes. ZIP archives remain on Firebird to avoid duplicating local storage. The initial transfer reported a missing supplementary `SELECTION.csv`; that table was copied separately and verified against `plan.json`. It was added beside the remote archive after packaging; the archive itself contains the authoritative `plan.json` and `RUN_INDEX.csv` selection records. No run artifact was missing from the verified local delivery.

QA evidence is in local `outputs/dyadic_pilot25_20260930/qa/` and remote `logs/qa_all/`, including exact decoded frame-3005 images and the corresponding table rows for A1/B2. The Google laboratory notebook's “2026 aggression” tab records the selection, execution, unresolved episode, and completion.

Package-note revision 2 clarified the global-frame interpretation after visual inspection and added the supplementary selection CSV to the full archive. The original archive and `RELEASE_RECEIPT.review_note_v1.json` are retained for provenance. The 775 scientific run files and their hashes are unchanged; `RELEASE_RECEIPT.json` points to the current archive. Local `LOCAL_VERIFICATION.initial.json` preserves the full transfer check, and `LOCAL_VERIFICATION.json` records the revised note/index and receipt hashes.
