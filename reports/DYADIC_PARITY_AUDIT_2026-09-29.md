# Dyadic review and shared-pipeline audit — 29 September 2026

Status: local development changes, not a new scientific release. Official dyadic and GroupTrial outputs remain PSC 1.5.1 / processor 0.8.1-group / viewer v3 and UNREVIEWED. No source TOMLs, tracking files, published bundles, or old ZIPs were modified.

## Confirmed defect and correction

The shared PSC model merged entities that selected the same detection within the movement/reacquisition gate, without an independent social-proximity check. A two-frame reproduction with beetles 90 pixels apart, a 60-pixel social radius, and one disappearing beetle produced PSCP in 1.5.1.

Local model 1.5.2 now requires proximity evidence before a new merge or former-partner rejoin: current raw positions if both exist, otherwise supported positions in the immediately preceding frame. The radius remains configurable and defaults to 60 pixels; the 100-pixel movement allowance cannot substitute for contact evidence. Connected proximity links support larger groups. If separate components compete for one blob, only one uniquely raw-supported component can retain it; unresolved components stay missing. Existing supported groups can still persist across missing detections under the existing rules. New events record MERGE_REJECTED_NO_PROXIMITY.

Tests cover the inclusive 60-pixel boundary, rejection at 60.01 and 90 pixels, stale prior proximity, conflicting coordinates associated with one blob, and the same restriction with six beetles. These tests establish software behavior, not biological validity.

## Dyadic versus six-beetle findings

| Feature | Finding | Local action |
| --- | --- | --- |
| PSC rules and thresholds | Both use persistent_groups.py and six_beetle_processor.py through run_group_pipeline.py. The official PROCESSOR_PARITY.json reports identical rules and parameters. The defect is shared. | Fixed centrally, versioned as 1.5.2. |
| HTML/video identification | Both used generic interaction_review.html and review_video.mp4. A run label could omit the cell. | Viewer v4 uses the original TOML stem, displays a dedicated cell/source-TOML line, and records both in its manifest and payload. |
| Regular PDF naming | Dyadic batch commands explicitly requested opaque task-ID filenames. GroupTrial used readable trial labels. | With --source-toml, the shared pipeline uses its original stem for the PDF, overriding old task-ID names. The PDF's label also uses that stem. |
| Outlined PDF naming | Both use render_psc_outlined_pdf.py, deriving its name from the regular PDF. | Inherits the corrected stem and retains __PSC_paths_outlined.pdf. |
| Source TOML propagation | The older dyadic worker omitted --source-toml; the official 7200-frame runner supplied it. The builder did not consume it. | Worker and shared builder now carry the source path. Both GUI profiles expose an original-TOML field and forward it. The field is cleared on session changes; source filenames are not guessed from session timestamps. |
| Raw/PSC comparison, uncertainty, human review | Same viewer/editor in both pipelines. | Retained. Human-reviewed rebuilds now retain source TOML identity and video orientation metadata. |
| Video orientation | Both current automatic routes use the same geometry planner. Human-review replay previously dropped geometry. | Corrected replay metadata propagation. |
| Frame windows | Official dyadic runs use 7200 inclusive observations; GroupTrial uses 9000. | Intentional dataset difference, unchanged. |
| CSVs, provenance and UNREVIEWED status | Shared raw/PSC tables, output dictionary, hashes and review status are present in both. | Dictionary now reads actual viewer filenames and documents cell/source fields. |
| Historical packagers | Version-specific dyadic packagers and release checks hard-code 1.5.1/v3 directories and generic filenames. | Retained as historical reproducibility scripts. Do not use them for a new 1.5.2 release without a versioned successor that reads actual manifest filenames. The generic review rebuilder writes new v4 directories. |

## Naming contract

Given Camera_2_40359705_20260702_1536_FIGHT_ACT2_A1.toml, new shared-pipeline outputs use:

- Camera_2_40359705_20260702_1536_FIGHT_ACT2_A1__interaction_review.html
- Camera_2_40359705_20260702_1536_FIGHT_ACT2_A1__review_video.mp4
- Camera_2_40359705_20260702_1536_FIGHT_ACT2_A1.pdf
- Camera_2_40359705_20260702_1536_FIGHT_ACT2_A1__PSC_paths_outlined.pdf

The HTML references the matching video filename. Full stems are retained to avoid collisions across recordings. Missing source metadata is explicitly displayed as not recorded; a source cell is never invented from a generic label. Legacy CLI calls without --source-toml use the supplied display label for filenames.

## Live source check and unresolved episode identification

A read-only SSH check confirmed the official dyadic RELEASE_RECEIPT.json on Firebird still describes 99 trials, 7200 frames each, PSC 1.5.1, viewer v3, UNREVIEWED, and archive SHA-256 2064ff0d95b2774da35f94122080d7842d02ae7f25f413aa88bb5cc76524f66b.

Read-only inspection of all nine matching official frame tables found beetle 0 PSCP_BLOB at global frame 3005 in **A1 and B2**; the other seven cells have both identities ASSIGNED. Therefore the recording name and frame alone do not distinguish the user's exact episode. The 90-pixel reproduction proves a shared code defect, but does not yet prove that it caused the observed A1 or B2 episode. Exact-cell/video review and a new versioned reanalysis remain necessary before claiming that episode corrected.

## Validation and release boundary

The full local suite passed 140 tests after the implementation and methods update. A subsequent six-beetle regression and updated source-identity tests were checked with the affected test modules. The original released outputs have not been renamed or regenerated; they continue to exhibit the old behavior. A new scientific release requires new output roots, manifest-driven packaging, hash/frame-count/PDF/ZIP checks, and visual review of the reported episode. Automatic results must remain UNREVIEWED.
