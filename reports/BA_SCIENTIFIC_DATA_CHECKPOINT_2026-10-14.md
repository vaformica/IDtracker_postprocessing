# BA scientific data checkpoint

**14 October 2026 | Human review: VAF | Report prepared by Codex**

## What is ready

Vince has approved **180 BA cells from 14 original recordings** as the tracking set to use for scientific data extraction. The catalog selects exactly one tracking version per cell and retains **41 excluded cells** in a separate audit. It combines the earlier 221-cell QC pass with the newly returned review of Savannah’s 11 reruns. These are cell-level assay records, not yet a count of unique biological animals; the animal metadata join remains to be defined.

Of the 180 approved cells, **176 have no movement hold**. Four earlier approvals—BA_059, BA_092, NEW_041 and NEW_088—still have unresolved-jump movement holds in their saved analysis files. Their approvals are preserved, but movement values must remain unavailable unless an explicit reviewed override or correction is supplied. No such override was added at this checkpoint.

The next step is to extract the outcomes Vince has now specified: **time near the wall, time on fungus, latency to move, and total distance traveled**. Time and latency should remain in frames; distance should remain in original-image pixels, summed from adjacent-frame steps. This checkpoint freezes the input selection and provenance. It does not yet create the final outcome table.

## The approved videos and data

Use these lists to select the correct versions, rather than selecting files by their names or modification dates:

- [Browse the 180 approved cells](../provenance/ba_science_selection_20261014/APPROVED_VIDEOS.html): readable list of source video/cell, selected version, frame window, review coverage and movement status.
- [Approved-cell catalog](../provenance/ba_science_selection_20261014/APPROVED_CELLS.csv): all 180 approvals, including the four movement holds; exact source paths, hashes and review IDs.
- [Movement-ready catalog](../provenance/ba_science_selection_20261014/MOVEMENT_READY_CELLS.csv): the 176 approved cells without a current movement hold.
- [Excluded-cell catalog](../provenance/ba_science_selection_20261014/EXCLUDED_CELLS.csv): all 41 exclusions and their attributed notes.
- [Complete selection and provenance](../provenance/ba_science_selection_20261014/SELECTED_PROVENANCE.json): selected manifests, exact decisions, original/submitted TOML information, arena polygons and rerun lineage.
- [Frozen numerical data](../outputs/ba_science_selection_20261014/frozen_data/): approved coordinate arrays, frame tables, QC sidecars and processing-code snapshots. [File hashes](../provenance/ba_science_selection_20261014/FROZEN_DATA_SHA256.json) identify every archived file.
- [Returned rerun review JSON](../outputs/ba_science_selection_20261014/BA_Savannah_reruns11_QC_20261014.json) and [all original review exports](../provenance/ba_science_selection_20261014/original_reviews/): immutable human-review records.

These relative links resolve within the local repository or a matching archive layout. The Firebird archive location is `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_science_selection_20261014`. It requires lab access; it is not a public download address.

## What changed in the rerun review

Savannah supplied 12 revised TOMLs. Eleven were run through IDtracker and the frozen BA recovery/interpolation/QC workflow; VAF approved nine and rejected two. The selected source filenames and hashes are recorded in the catalogs and the [rerun completion record](BA_SAVANNAH_RERUNS_2026-10-14.txt).

| Rerun cell | VAF decision | Consequence |
| --- | --- | --- |
| BA_035, BA_049, BA_070 | Approved | Select the October 14 rerun |
| NEW_017, NEW_020, NEW_022 | Approved | Select the October 14 rerun |
| NEW_046, NEW_059, NEW_072 | Approved | Select the October 14 rerun |
| NEW_015 | Excluded | VAF: “Start of video missing.” |
| NEW_021 | Excluded | Tracking jumps; 21 residual jumps and 3,088 missing positions |

BA_065 was skipped at Vince’s request because its revised tracking interval was empty. No revised NEW_093 TOML was found. Both retain their prior exclusion decisions. The five reruns from the June 27, 16:14 ACT2 recording preserve the previously requested exclusion of global frames 1608–1609. Revised start frames are retained exactly; notably NEW_020 begins at 1096 rather than its previous start of 10. A tracking start is not automatically the biological start of death feint or the start of the assay.

## Provenance and interpretation

Each approved row is bound to a dataset fingerprint and an attributed review ID. Its manifest identifies the original video, source/submitted TOMLs, IDtracker trajectory/session, arena, inclusive global-frame window and processing rules. Parent-to-rerun links preserve the earlier tracking and review history. No approval was inherited by changed tracking, and no rejected rerun falls back to an older version.

The approved set contains **172 trace skims, six trace-plus-full-video reviews and two trace-plus-excerpt reviews**. These are the recorded scopes of VAF’s approval. They must not be described as frame-by-frame behavioral ground truth. Track approval also does not establish the accuracy of automatic turtling duration: earlier human scoring found substantial missed posture episodes. Automatic posture masks remain screening evidence, and the viewer’s adjustable 15% threshold has not been adopted as a scientific exclusion rule.

The frozen coordinates distinguish raw IDtracker positions, image-supported recovery and interpolation. **STRICT_ANALYSIS.npz is the movement-facing coordinate layer.** FRAMES.csv contains pre-strict interpolated analysis coordinates and must not be used to bypass the strict jump gate. Both endpoints of unresolved large jumps remain unknown; movement holds remain explicit. Missing or human-excluded frames are unknown, not zero activity or negative posture. Coordinate units are original-image pixels; frame indices are zero-based and window endpoints are inclusive. Each selected window contains 7,200 frame observations and at most 7,199 adjacent-frame steps.

Provenance verification matched all 221 selected manifests and their reviewed artifacts. A [read-only Firebird source audit](../provenance/ba_science_selection_20261014/FULL_SOURCE_AUDIT.json) matched **685 existing source fingerprints** and newly fingerprinted all **14 original recordings** (167,700,143,978 bytes). Newly recorded video hashes identify the current source bytes; they cannot retroactively establish an absent historical video hash. The frozen numerical archive contains 1,845 files with recorded SHA-256 hashes. The BA suite passed 143 Python tests and 11 JavaScript test scripts. These checks establish file/software integrity; VAF’s decisions supply the human approval.

## Next steps: extract the four requested outcomes

Codex should implement a separate, versioned extractor that consumes the approved catalog and exact frozen coordinate hashes. It should not regenerate tracking, silently change the selected windows or reuse older summary CSVs from another coordinate version. Before calculating the final table, settle the few remaining definitions below.

| Requested outcome | Raw output | Definition to fix before extraction |
| --- | --- | --- |
| Time near wall | `wall_frames` | Count eligible positions inside the arena and within a chosen wall band. The older BA route uses a 30-pixel band; that is an existing setting, not a newly adopted scientific threshold. |
| Time on fungus | `fungus_frames` | Count eligible positions within an explicitly mapped fungus polygon. Current BA inputs contain only the arena ROI, and the older BA route does not calculate fungus metrics. Confirm fungus is present and identify its region; unavailable geometry must yield missing/not assessed, never zero. |
| Latency to move | `latency_to_move_frames` and `movement_onset_global_frame` | Define the biological starting frame and criterion for movement. The older prototype measures first displacement of at least 30 pixels from the exact starting coordinate through an uninterrupted valid chain; it is not first nonzero motion. A sustained-departure rule is a different definition and must not be substituted silently. |
| Total distance traveled | `total_distance_px` | Sum Euclidean displacement over eligible consecutive frame pairs. No crossing gaps, excluded frames or held jumps. Distance has pixel units, even when calculated from raw frame-indexed data. |

For latency, later TOML starts can omit part of the initial event. Preserve an explicit left-censored/not-estimable state when the biological origin is unavailable. If movement never occurs in an otherwise assessable window, record the observation limit and a right-censored status rather than assigning zero latency. Missing data before a possible onset must remain distinguishable from “did not move.”

The proposed extraction handoff has three parts:

1. **Approve the definitions.** Choose full-window versus post-movement summaries, wall width, fungus geometry, movement criterion and treatment of recovered/interpolated positions. Use the complete 7,200-frame selected window as the documented input unless Vince chooses a different observation window. Decide how the four movement-held cells should be handled without changing their saved approvals.
2. **Build and inspect a small extraction pilot.** Include an ordinary approved track, an interpolated track, an excluded-frame case and a held-movement case. Check a wall crossing and movement onset against the source images. If fungus applies, verify its polygon and boundary membership in the same source coordinate system. Test known synthetic counts/distances and missing-data cases before running the entire set.
3. **Export the full scientific tables after that check.** Produce one frame table with global frame, selected x/y, coordinate provenance, wall/fungus membership and eligible step distance; one cell-level table with the four requested outcomes, window boundaries, valid/unknown frame counts, valid step counts, censoring/status fields and review IDs; and a manifest with code version, parameters and all input/output hashes. Report recovered/interpolated contributions separately so their inclusion can be evaluated. Keep time as frame counts and distance as pixels; do not silently convert to seconds, physical length, rates or percentages.

These steps make the analysis reproducible while keeping Vince’s scientific choices explicit. The approved tracking set is ready for this extraction-development stage; the next deliverable should be a checked pilot of the requested variables, followed by the full table under the agreed definitions.
