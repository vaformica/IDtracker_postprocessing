BA cells selected for scientific extraction — 14 October 2026
AI-written record by Codex from VAF’s saved decisions and explicit instruction to use the approved cells for science.

This checkpoint selects 180 approved BA cells from 14 source recordings. There are 41 excluded cells. Savannah’s 11 revised TOMLs produced nine newly approved replacements and two rejected replacements (NEW_015: “Start of video missing”; NEW_021: tracking jumps). An explicit rerun lineage selects the replacement version; historical approvals and rejections are preserved rather than copied or erased. BA_065 was skipped at Vince’s request, and no revised NEW_093 TOML was found; their previous exclusion decisions remain selected.

The approved list is the authoritative track-selection checkpoint, not a final analysis table. Of its 180 cells, 176 currently have movement extraction available. BA_059, BA_092, NEW_041 and NEW_088 retain explicit movement holds from unresolved jumps. Their human approvals remain intact. No movement override was supplied in the returned decisions, so those four cannot silently contribute numerical movement measures. Frozen coordinates and unknown frames are retained for all 180 approved cells.

VAF’s recorded review coverage is 172 trace skims, six trace-plus-full-video reviews and two trace-plus-excerpt reviews. Preserve these distinctions in methods: this is a human-approved tracking set, not frame-by-frame ground truth. Approval does not validate frozen automatic turtling durations. In particular, prior human review demonstrated missed posture episodes; automatic candidates are screening annotations. The selectable 15% review cutoff is not adopted here as an analysis exclusion rule.

What is frozen
Each selected record identifies its source video and cell/census locator; exact original and submitted TOML information; arena polygon; inclusive global frame window; IDtracker trajectory and session; recovery and interpolation rules; strict coordinate layer; review ID, reviewer, date, scope, notes, flags and original export hashes. SELECTED_PROVENANCE.json contains the full manifests and decisions. Original review JSON bytes are preserved in original_reviews/. The output list has one selected version per source cell, with all 11 parent-to-rerun links retained. A source cell locator is not yet a biological animal ID; linking to animal metadata is a separate analysis step.

The frozen data archive contains COORDINATES.npz, STRICT_ANALYSIS.npz, FRAMES.csv and their evidence sidecars plus the original processing-code snapshots. Raw, recovered and interpolated positions remain distinct. STRICT_ANALYSIS.npz is the movement-facing layer: FRAMES.csv analysis_x/y are pre-strict interpolation output and must not bypass the strict movement gate. Keep human-excluded frames and unresolved positions unknown. Do not bridge their gaps or turn unavailable movement into zero. Source coordinates are original-image pixels; global frame indices are zero-based and windows include both endpoints. Review videos are cropped derivatives, not calibrated source images. Physical units and assay time origin still require definition.

Files to use
APPROVED_CELLS.csv: all 180 human-approved versions, including the four movement holds.
MOVEMENT_READY_CELLS.csv: the 176 approved versions without a movement hold.
ALL_SELECTED_CELLS.csv and EXCLUDED_CELLS.csv: the complete selection and exclusion audit.
SELECTED_PROVENANCE.json: full source manifests, review decisions and rerun lineage.
FROZEN_DATA_SHA256.json: file-by-file hashes for the separate numerical archive.
FULL_SOURCE_AUDIT.json: current full hashes of source recordings, TOMLs, sessions and trajectories; new hashes cannot retrospectively prove previously unhashed video identity.

Next scientific decision
Vince will decide which biological variables to extract. Before implementation, define the assay time origin, observation window, treatment of initial death feint, activity thresholds, wall/interior geometry, missing-data denominators, inclusion of recovered/interpolated positions, posture measures and animal metadata join. Recovery latency, activity and spatial use remain possible questions, not adopted outcomes. This checkpoint does not recompute historical summary metrics or generate a final publishable outcome table.

Storage
Versioned local data: outputs/ba_science_selection_20261014/frozen_data.
Versioned Firebird archive: /data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_science_selection_20261014.
Source videos, original TOMLs, prior tracking and previous review packets remain unchanged. The live review database stays on local disk; closed snapshots are archived. Git stores code, source manifests, original review exports and the selection tables; the numerical data archive is separately hashed. The Git checkpoint freezes the current BA implementation; exact historical processing bytes remain in each packet’s frozen code directory.

Verification at this checkpoint
All 221 selected run manifests and their reviewed artifacts matched. The read-only Firebird audit matched 685 existing source hashes and newly fingerprinted 14 complete original recordings (167,700,143,978 bytes); no source mismatches occurred. BA regression tests: 143 Python tests and 11 JavaScript test scripts passed. These are provenance/software checks; VAF’s saved decisions supply the human approval.

Later instruction on October 14: Vince selected wall time, fungus time, latency to move and total distance traveled as the next outcomes. See reports/BA_SCIENTIFIC_DATA_CHECKPOINT_2026-10-14.md for the updated extraction plan, frame/pixel units and remaining operational definitions.
