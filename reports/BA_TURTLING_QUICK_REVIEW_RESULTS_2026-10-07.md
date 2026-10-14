# The five-clip BA check matched the submitted human scores

VAF returned all five completed decisions from the [quick review](BA_TURTLING_QUICK_REVIEW_2026-10-06.md). The frozen detector predictions agree with the submitted posture labels on every displayed frame. No detector parameters or production defaults were changed.

| Review material | Submitted human label | Frozen prediction |
| --- | --- | --- |
| Clip 1: complete run, frames 684–7883 | No turtling | No turtling |
| Clip 2: complete run, frames 822–8021 | No turtling | No turtling |
| Clip 3: short scene, frames 7305–7904 | No turtling | No turtling |
| Clip 4: short scene, frames 2840–3439 | No turtling | No turtling |
| Clip 5: short scene, frames 6860–7459 | Turtled at 7010–7459 inclusive | Turtled at 7010–7459 inclusive |

Across these 16,200 reviewed frames, there are 450 matching positive frames (15 seconds), 15,750 matching negative frames, zero extra predicted frames, and zero missed labeled frames. These are comparisons with VAF's submitted annotations, not an automated claim of biological truth.

## What this establishes—and what remains open

The two complete runs had predictions hidden and provide useful checks for missed events in those specific runs. The three short scenes showed suggestions; the positive interval in clip 5 was saved as a manual decision with the same bounds as the suggestion. It is a guided confirmation, not a blind positive test. Only one of the five source recordings was entirely new to this development work.

Clip 5 ends at frame 7459 while the positive interval is still open at the clip boundary. This label confirms the displayed portion only. It does not establish when the beetle rights itself, or whether it remains turtled for the rest of its source window, which ends at 8738. The frozen prediction continues beyond the clip; that continuation is still unreviewed. No flailing labels were collected.

These results support keeping the current rules for the next check. They do not erase the disagreements remaining in the earlier 12 development runs, or establish an error rate across all BA videos. The next useful check is the continuation of this positive event, followed by additional onset/end and quiet-on-back examples from unused runs. Keep broad deployment separate from this small review result.

## Preservation and verification

The original uploaded JSON is preserved byte-for-byte, including attribution, revision history and export time (`2026-10-07T12:57:48.663Z`). Its SHA-256 is `b0eff574b33cd0e6670b89af5467d113595af350306ebc56085f4185c4fe9565`.

The comparison verified the scoring-set fingerprint, exact clip list, inclusive frame bounds, completion flags, agreement between exported annotations and saved state, and hashes of the frozen selection and all five prediction files. It compared the hidden full-run predictions as well as the guided suggestions, using only the displayed windows. No blank, unfinished or uncertain decisions were interpreted as negative; none were present in this upload.

Evidence folder: `outputs/ba_turtling_quick_review_results_20261007/`. The same-named folder under Firebird's `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/` holds the preserved scores, reproducible comparison, report and delivery checks. Prior review packages and predictions remain unchanged.
