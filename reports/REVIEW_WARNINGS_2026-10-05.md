# Warning-guided review packages — 5 October 2026

> **Current-status cross-reference (15 October 2026):** Six-beetle development is on hold until Charlotte needs network or time-on-fungus data. There is no automatic October 19 or two-week restart. See [the current handoff](../SIX_BEETLE_README.md). The dated report below is preserved as history; reminder and workflow statements are not current authorization. Outputs remain UNREVIEWED.

Vince paused correction-editor development and requested a practical way for Hannah and Charlotte to find portions of the existing reviews that need closer inspection. The new packages add warning summaries and frame links to the 25 dyadic and 26 six-beetle reviews. They retain PSC 1.6.0 / processor 0.8.2-group; no scientific trajectories, videos, PDFs, or scientific CSVs were recomputed.

The six-beetle collection contains 101 adjacent-frame raw centroid jumps greater than 100 original-video pixels, across 20 of 26 trials. The dyadic collection contains three, across three of 25 cases. Box01 MIX from groupagetrial04 has ten. These counts identify review priorities, not confirmed ID mistakes. Smooth identity swaps can escape a jump rule, and a flagged jump does not establish which beetle is correct.

Each START_HERE page includes the jump count (with a greater-than-200-pixel subset), distant returns after missing detections, raw missingness, missing-ID and inferred-position bouts lasting at least one second, and the processor's ambiguity/conflict flags. Warning events name the zero-based ID and global frame. Clicking a frame opens the existing review at that location. Review before and after the flagged interval. Distant returns are explicitly separated from adjacent-frame jumps; overlapping warning categories are not independent errors.

All outputs remain **UNREVIEWED**. The correction editor remains paused at 0.3.0, with an October 19 reminder pointing to the Box01 frame-855 example and the preserved IDtracker Validator alternative.

Local packages: `outputs/psc_review_qc_20261005/`. Authoritative Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/psc_review_qc_20261005`. The existing shared Dropbox folder receives new `QCwarnings_v1` individual ZIPs and an updated download index; older packages and the previous index are retained.

Verification records are `QC_VALIDATION.json`, `QC_RELEASE_RECEIPT.json`, per-run `QC_PROVENANCE.json` and `QC_FILE_CHECKSUMS.json`, plus Dropbox upload receipts. Checks verified 1,632 original files unchanged, all 51 canonical/manifest bindings, exact unrounded jump counts, ZIP integrity, 4,077 local links without broken targets, and a browser frame-link test at global frame 1726. Two focused QC tests passed. Both full collection archives are CRC-tested on Firebird. These are software/delivery checks, not biological validation.

The reproducible packaging scripts are `build_review_qc_packages.py`, `finalize_review_qc.py`, and `build_qc_collection_archives.py`. The finalizer fixes navigation in viewers that lack a closing body tag and refreshes package checksums without changing scientific arrays.
