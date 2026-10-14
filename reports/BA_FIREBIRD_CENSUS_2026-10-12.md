# BA tracking completeness and Firebird census — October 12, 2026

AI-written audit by Codex. This report separates missing tracked coordinates within analyzed videos from configurations lacking confirmed tracking or analysis. It does not establish biological validity or approve automatic turtling labels.

## Missing tracking in the current 121-run review set

85 runs have all 7,200 coordinates available; 36 have at least one missing position. Of those 36, 23 have ten or fewer missing positions, seven have 11–100, and six exceed 100. Missing tracked positions do not imply missing video images. Missing posture remains unknown.

BA004 is the clear priority: 2,517 / 7,200 positions are missing (34.96%), spread across 497 gaps. Its longest gap is 152 frames, global frames 5074–5225. The source is Camera_2_Straw_40359705_20260716_1514_EPOCH_BA_C2.toml. Recovery is unresolved, so an absence of detected turtling is not a reliable negative. Inspect the footage and segmentation across several gaps before deciding whether to retrack.

| Run | Missing positions | Missing % | Longest gap (frames) | Number of gaps |
|---|---:|---:|---:|---:|
| ba_004 | 2517 | 34.96% | 152 | 497 |
| ba_069 | 258 | 3.58% | 89 | 31 |
| ba_055 | 206 | 2.86% | 26 | 111 |
| fresh_04 | 141 | 1.96% | 85 | 22 |
| ba_015 | 136 | 1.89% | 73 | 46 |
| ba_067 | 118 | 1.64% | 29 | 23 |

Across all 121 windows, 3,733 / 871,200 positions are missing (0.43%). Excluding BA004, the remaining 120 windows have 0.14% missing. The pooled result hides BA004's problem. Small gaps warrant targeted review; they are not automatic exclusions. Large jumps and camera bumps are separate flags and can occur when no coordinates are missing. The visual causes of these losses have not been diagnosed by this census.

## What exists on Firebird

The recursive census enumerated 341,140 files in the lab and user home research trees, including 4,053 TOML files. Of 3,829 IDtracker-style configurations, 1,229 specify one animal. Grouping exact parsed arena, video basename and tracking start yields 323 configuration groups, including 299 represented in the main BA video collection. These are configurations, not 323 independent animals: older settings, revised arenas, source/rotated videos and copied inputs must be reconciled before making a biological trial count.

Within the 299 main-collection configurations:

- **41**: Unspecified source start; readable tracking exists.
- **18**: Nearby arena match only; reconcile settings before reuse.
- **100**: Compatible tracking available; no confirmed analysis record.
- **121**: Completed analysis record and frame output found.
- **3**: Unspecified source start; session exists but trajectory absent.
- **15**: No matching or nearby tracking session found.
- **1**: Exact arena match; segmentation settings differ.

Thus 221 configurations have a compatible readable 7,200-frame tracking window, and 121 also have a completed-analysis record with an existing frame-data output. The other 100 are candidates for analysis using existing tracking, subject to trial/version reconciliation and QC. “No confirmed analysis record” is not proof that no older analysis ever existed: this audit recognized specific completion records and frame outputs, not every legacy naming convention. This is also not a new release check of PDFs, MP4s or ZIPs.

The 44 configurations with unspecified source starts already have corresponding sessions: 41 have readable trajectory arrays, while three have no trajectory at the expected paths. Those three are Camera_2_40359705_20260628_1604_ACT2 cells C1, C2 and C3. Their starts must be resolved before assigning the intended BA window; recorded session start zero was not silently adopted.

Eighteen configs have near-identical arena candidates for the same video (June 29 Camera 1 ACT1), with bounding-box differences of roughly 1–4 pixels. These are plausible existing tracking matches, not confirmed exact matches. A separate Straw A2 case has the same arena but an intensity threshold difference (34 versus 36). Preserve those distinctions before reuse.

Fifteen configurations (14 distinct source filenames) have no exact or nearby same-video session match: June 27 Camera 3 ACT1 cells B4, C1, C2, C3, C5; June 28 Camera 3 ACT2 cells A3, A5, B1, B2, B3, C2, C3; and Straw BA cells B1 and C1 (B1 has two configurations). These are the strongest candidates for missing tracking, but orphaned/renamed results or records inside archives remain possible. Check submission histories before scheduling replacements.

## Other possible BA TOMLs

The 24 additional configuration groups outside the main BA folder comprise 20 automated segmentation drafts, three historical pipeline input snapshots, and one software test fixture. The 20 drafts all point to already-known BA recordings and have nearby session candidates. They should not become extra animals in the dataset. No separate one-animal recording collection was identified outside the main BA collection in the searched trees. One animal alone is not proof of the experimental treatment.

## Scope and next steps

Searched /data/labs/vformic1-swat-lab and /home/vformic1-swat recursively. The formicalab aliases point into those trees. All 66 skipped directory symlink targets lie within the covered roots. All 138 parser errors are AppleDouble `._` metadata files, not readable source TOMLs. Software environments, browser/key/cache folders, other labs/users, unmounted storage, node-local temporary files and compressed archive contents were excluded. This is a census of the accessible lab research storage, not every user's data across the cluster.

1. Inspect BA004's recurrent losses and recovery state, then decide whether segmentation/retracking can help.
2. Resolve canonical trial identities and rotated-video versions; reuse compatible tracking for the additional analysis candidates.
3. Reconcile unspecified starts, the 18 near-matching arenas and Straw A2's settings.
4. Inspect missing-session/submission histories and the three sessions without trajectories, then submit only the genuinely absent or unusable tracking.
5. Build a completion ledger for every canonical BA trial. Retain uncertainty flags and keep turtling outputs UNREVIEWED; the focused BA060 review already demonstrated a substantial missed onset.

No new IDtracker batch was launched by this audit. No source TOML, trajectory or previous result was modified. Jobs 918306, 918308 and 918309 were read-only census/matching jobs.

Evidence: RAW_CENSUS.json (paths and hashes), CENSUS_MATCHES.json (exact-match checks), RECONCILIATION.json (nearby-arena candidates), ACTION_INVENTORY.json (action lists), MISSING_TRACKING.json (all 36 gap records), and the preserved scan/matching scripts under outputs/ba_firebird_census_20261012. Firebird holds the same audit folder under idtracker_pipeline_runs.
