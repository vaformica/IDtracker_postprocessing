# Dyadic turtling candidates in general QC — October 15, 2026

The existing 25 dyadic runs now have a new local dashboard combining tracking warnings with possible-turtling review. Open http://127.0.0.1:8797/dyadic_general_qc_20261015/START_HERE.html while the local server is running. Files are under `outputs/dyadic_general_qc_20261015/`. This dashboard depends on the unchanged sibling `psc_review_qc_20261005` packages; it is not a portable or newly shared download.

The 25 cases contain 142 candidate bouts across both identities. These are review workload, not confirmed turtling events. The motion screen uses quiet/looping raw centroid patterns. Upright stops and fighting can trigger it, and real turtling can be missed. The image classifier is not used. Near-partner and missing-partner candidate frames remain visible with separate context counts, rather than being discarded. Missing target tracking is unknown. No biological turtling duration is exported.

Each General QC page links prominently to its turtling section. The latter shows X/Y traces for each raw ID, gold candidate bands, inclusive global-frame ranges, quiet/loop support, partner context, and an embedded existing video reviewer. Clicking a candidate seeks that video to its first frame. IDs are 0/1 in turtling/video; existing general QC uses Animal 1/2, with the mapping explicitly explained. Human review scores have not been auto-applied. Existing video correction controls concern PSC, not confirmation of posture; use the separate posture scoring workflow for attributed posture labels.

`dyadic_turtling_qc.py` 0.1.0-candidate-qc wraps frozen `dyadic_turtling_experiment.py` 0.1.0-development. `unified_qc.py` 0.2.0-development automatically writes linked candidate JSON/HTML sidecars for two-animal inputs. One-animal BA and six-animal runs do not receive these sidecars. Non-30-fps input is explicitly NOT_ASSESSED because the frozen screen is frame-based. Source hashes, code hashes and screen parameters are retained. The GUI deployment list includes both dependencies; no Firebird deployment or new tracking run was performed.

Rebuild with the runtime Python containing NumPy:

```
python build_dyadic_turtling_qc_dashboard.py --output outputs/NEW_VERSIONED_FOLDER
python serve_review.py outputs --port 8797
```

The builder checks all 25 canonical source hashes and preserves source artifacts. General QC is replayed on existing raw tracking; recording disturbance scans remain NOT_ASSESSED. All 25 sidecar pairs and their links were checked; browser testing confirmed embedded video loading and candidate 7032 seeking to global frame 7032. Focused screen, sidecar and unified-QC tests cover missing data, near/unknown partners, global ranges, immutable inputs, unsupported fps and dyadic-only integration. These checks establish software behavior, not biological accuracy.

The saved detector checkpoint is commit `f10a917`. This integration supersedes the earlier handoff's statement that QC integration was not yet implemented. Production PSC 1.6.0 / group processor 0.8.2-group, original scientific CSVs/PDFs and prior human scores remain unchanged. Six-beetle development remains on hold.
