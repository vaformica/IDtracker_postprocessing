# PSC 1.6.0 regenerated review collection — 5 October 2026

> **Current-status cross-reference (15 October 2026):** Six-beetle development is on hold until Charlotte needs network or time-on-fungus data. There is no automatic October 19 or two-week restart. See [the current handoff](../SIX_BEETLE_README.md). The dated report below is preserved as history; reminder and workflow statements are not current authorization. Outputs remain UNREVIEWED.

Status: **COMPLETE_UNREVIEWED**. This is a software-verified review collection, not biological approval.

## Scope and versions

All 25 previously selected dyadic cases and all 26 six-beetle trials were regenerated using PSC **1.6.0**, group processor **0.8.2-group**, raw/PSC viewer **v4**, and **outlined-psc-v1** PDFs. The 99-run dyadic set remains withdrawn and was not rerun. Dyadic windows contain 7,200 inclusive frames and six-beetle windows 9,000, beginning at each source TOML tracking start.

Available IDtracker identities retain their exact input positions and return immediately when detected. Assigned-centroid proximity uses 60 original-video pixels. PSC inference is limited to missing IDs with supporting context/evidence; it is not directly observed contact. Upstream identity swaps remain review questions.

## Files and access

Authoritative Firebird root:
`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/psc_1_6_0_regenerated_51_20261005`

Local master index:
`outputs/psc_regenerated_51_20261005/review_set/START_HERE.html`

[Private Dropbox review folder](https://www.dropbox.com/scl/fo/7osk6ybg44ay37b2kxuow/AGXADcYWgtGwOp-k8HgIpS4?rlkey=799agf7zg6xdw0fspc3o62a5o&dl=0)

Dropbox confirmed viewer access for Hannah Donald (`hdonald1@swarthmore.edu`) and Charlotte Greene (`buk3nk@virginia.edu`), with downloads enabled and no sharing errors. These are private links requiring direct folder access; invitations/access grants do not establish that either collaborator has opened them. Manage or revoke access through Dropbox’s folder sharing controls.

The folder contains 51 individually downloadable case ZIPs, a searchable `START_HERE.html`, `DOWNLOAD_INDEX.csv`, `SHARING_MANIFEST.json`, and `READ_ME_FIRST.txt`. Download a case ZIP, unzip it, and open its `START_HERE.html`. No Firebird login or Python installation is needed. The downloaded master HTML links to the private Dropbox case downloads. Individual ZIPs are under 100 MB; two full collection ZIPs also remain on Firebird.

Each case ZIP and review media use the original TOML stem, including video and cell identity. Each case index links the HTML viewer, MP4, regular PDF, outlined PDF, and CSV index. The two collections together contain 51 videos, 51 review viewers, 102 PDFs, and all frame/summary CSVs. Sharing receipts and the Dropbox portal are also retained on Firebird.

## Validation and provenance

- 157 tests passed for the correction before regeneration.
- All 51 encoded MP4 frame counts, inclusive CSV windows, PDF versions/cell labels, and ZIP integrity checks passed.
- 1,683 downloaded run-file hashes and 1,226 local HTML links verified.
- All 51 canonical result arrays exactly match the separately verified PSC 1.6.0 regression replay, including positions, sources, inferred flags, groups, and ambiguity.
- Per-run source hashes and video size/mtime checks confirmed unchanged inputs.
- The frozen original code snapshot is retained. A documentation-only finalization repair registered `raw_identity_policy` in the output schema after the analyses/media had completed; `finalization_code/` and per-run `documentation_repair.json` record the repair without rewriting the analysis snapshot.

Authoritative receipts: `RELEASE_RECEIPT.json`, `CODE_SNAPSHOT.json`, `FILE_CHECKSUMS.json`, per-run manifests, `LOCAL_VERIFICATION.json`, `DROPBOX_FILE_RECEIPT.json`, and `DROPBOX_FOLDER_SHARE_RECEIPT.json` under the new collection or its local counterpart. Local Dropbox ZIP containers have separately recorded checksums; their verified scientific file contents match the authoritative collection.

Full collection ZIP SHA-256:

- Dyadic: `68851aa6468f876627373a2da00907bbf8cd47802dae7cf23f51fef95536700c`
- Six-beetle: `5db3cf32f44f53eb86d37cf32cdf28d053c962d1c5cbcf65bf7ad00e6ce87464`

## Superseded output withdrawal

The data-specific inventory identified 5,559 remote generated files (53,360,190,850 logical bytes) and 1,104 local generated files (4,146,662,850 logical bytes). These obsolete derived files have been removed. Original videos, TOMLs, IDtracker tracking, detection evidence, code snapshots, JSON/Markdown provenance, and attributed review records were protected. Logical byte totals are not a measurement of recovered physical disk space.

Local deletion is verified in `outputs/psc_withdrawal_20261005/LOCAL_DELETION_RECEIPT.json`. Remote deletion is also **DELETED_VERIFIED** in `psc_withdrawal_20261005/REMOTE_DELETION_RECEIPT.json`: all 5,559 targets are absent, and all 421 protected input files passed before/after preservation checks (200,665,573,158 bytes). Historical roots now carry withdrawal notices; their original receipts remain unchanged.
