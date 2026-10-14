# Run 12: additional human-confirmed turtling

VAF re-reviewed Run 12 and confirmed an additional on-back event at global frames **2908-3036 inclusive**. The unchanged detector had marked all 129 of those frames. This is a correction to the human reference annotations, not a detector improvement or a new rule.

Run 12 now has three human-confirmed posture intervals: 2908-3036, 4231-5862, and 7594-8737. Total human on-back time is 2,905 frames (96.833 seconds). The analyzed total remains 2,963 frames (98.767 seconds), with no missed human-confirmed frames and 58 extra frames. The newly confirmed interval does not establish flailing; that behavior is explicitly unreviewed for 2908-3036, while earlier flailing annotations remain preserved.

Across the 12 development runs, falsely flagged frames decrease from 239 to **110** (3.667 seconds) and missed frames remain **253** (8.433 seconds). Run 12's remaining extra intervals are 2887-2900, 2903, 3037-3052, 5863-5878, and 7583-7593. These remain disagreements against the current human annotations, not necessarily proven biological errors.

The original uploads, earlier normalized scores, detector outputs and previous charts are preserved. This new folder holds attributed amended scores, the updated comparison, and the regenerated 12-run graph. Input hashes and assertions verify that other runs and all detector predictions are unchanged. The PDF was rendered and visually checked.

This was detector-guided re-review within the development set; it does not provide independent validation. A next review should include candidate onset/end boundaries, some unflagged stretches, and complete previously unused runs to examine missed events. Freeze the rules before evaluating those runs, and report how runs share source recordings.

Local and Firebird evidence folder: `ba_turtling_run12_correction_20261006`. The full Firebird path is `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_run12_correction_20261006`.
