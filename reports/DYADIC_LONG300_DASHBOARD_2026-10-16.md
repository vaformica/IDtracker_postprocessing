# 300-frame candidates in the fight dashboard

AI-written by Codex for Vince, 16 October 2026.

Vince selected the 300-frame minimum after comparing 150, 200 and 300 frames.
The separate `dyadic_turtling_long_bouts.py` 0.1.0-long300-qc now supplies the
current fight dashboard's candidate layer. It does not replace the BA detector
or change shared PSC, raw trajectories, existing processing results or approvals.

The frozen context_300 rule uses localized looping in fully observed 120-frame
windows and localized quiet tails linked to loop support within 300 frames.
It suppresses the first 100 observations of each selected TOML window and raw
fungus occupancy, then retains continuous candidates of at least 300 frames.
Missing coordinates cannot enter a candidate. Wall proximity and a preceding
fall were evaluated in the experiment but are not required by the selected rule.

All 98 eligible fight packets were screened using full-precision raw coordinates
verified against their immutable packet hashes. The new layer contains 105
candidate intervals and 76,607 candidate frames; the previous 610-interval layer
is preserved. Four configuration holds remain. All 34 masks from the development
comparison replay exactly across 17 cells and three recordings.

On the explicit development labels, the selected rule covers 14,695/15,573
positive frames (94.4%) and flags 3,985/199,020 explicitly negative frames (2.00%).
Within the 11 human bouts lasting at least 300 frames, coverage is 14,129/14,257
(99.1%). These labels informed development; this is not independent validation.
Unannotated footage remains unknown, and candidate duration is not posture
duration. Human identity/posture confirmation is still required.

The operations repository contains `runs/fights_20261015/CURRENT_TURTLING_QC.json`
and `turtling_qc_long300_v1/` with the frozen source, runner, per-packet results,
input hashes, manifest and validation record. The dashboard verifies that pointer
and every sidecar against the exact source packet. Its annotation export retains
the candidate-manifest hash. Human records and the Firebird review-provenance
pointer are unchanged. This integration required no new tracking, base processing
or remote writes.

Six focused tests cover minimum length, global frame alignment, missing/fungus
gaps, initial suppression, quiet-only input, unsupported frame rates and input
preservation. The dashboard checks include candidate selection without human
label creation, per-ID traces, distance, typed boundaries and video scrubbing.
Browser appearance was not newly verified because file-URL control is blocked.

BA060 and BA030's documented misses remain unresolved. Six-beetle development
and identity-editor development remain paused. Saving their existing work in the
publication checkpoint does not resume either project.
