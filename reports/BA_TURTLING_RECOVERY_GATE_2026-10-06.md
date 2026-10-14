# BA turtling after death-feint recovery

Current human-score update: [Run 12 correction](BA_TURTLING_RUN12_CORRECTION_2026-10-06.md) adds 2908-3036. Detector predictions are unchanged; the latest 12-run comparison has 110 extra and 253 missed frames. The results below retain their original reference annotations.

VAF reconfirmed that Run 1 flips at **global frame 2834 and stays overturned through 8294**. The briefly stated 1177 onset was retracted before any scoring file was changed. The original posture and flailing annotations remain intact. VAF also explained that all beetles begin in death feint, and attributed the early tracking jumps to a bumped camera rather than animal movement.

This suggested a useful prerequisite: do not accept turtling candidates before the animal has recovered enough to move away from its starting location. The new, separate `ba_turtling_recovery_gate.py` experiment applies that idea to the previously tested 0.2.0 candidates. It does not change the production pipeline, raw coordinates, or existing wake results.

The existing BA distance threshold is **30 original-image pixels from the exact starting position**, not accumulated path length. The experiment requires 30 consecutive qualifying observations at 30 fps, with no missing position or incoming step above the existing 200-pixel jump limit. Eligibility opens on the final confirmation frame, not retrospectively at the first departure. Once open, returning to the initial position does not close it. The one-second confirmation is an experimental addition, not a previously validated biological rule.

Known initial camera artifacts receive an additional safeguard. Before testing departure, the tracked position must first remain within 30 pixels of the original reference for 30 reliable observations after the last marked artifact. A lasting camera offset therefore cannot itself confirm recovery in a run with a marked initial bump. Failure to reacquire the reference is explicitly unknown and requires review; it is not a confirmed absence of turtling. This conservative guard can also remain unresolved if a beetle genuinely moves away during the bump.

For Run 1, the raw steps above 200 pixels land at 1098 and 1099. Their camera cause is attributed to VAF; those frame numbers come from the trajectories. Sampled background comparisons do not show a lasting shift approaching 30 pixels, but they are not a camera-stabilization method or an independent confirmation of the cause. Other unmarked or later camera movements remain a QC limitation.

The prototype's wake calculation follows an unbroken chain from the exact starting frame. Those two early jumps break the chain, so it reports `THRESHOLD_NOT_REACHED` for Run 1. The separate eligibility experiment can assess later reliable tracking and confirms sustained departure at **1350**. Its result must not be substituted into the legacy wake column or interpreted as the exact biological moment of recovery.

## What the test changes

Across all 12 scored runs, the gate removes **149 falsely flagged frames (4.967 seconds)** and no correctly flagged frames. All of that improvement is Run 1's early 1177-1325 false event. Its real 2834 onset is retained, as are all other previously detected true intervals.

| Comparison across 12 runs | Previous 0.2.0 | With recovery gate |
| --- | ---: | ---: |
| Falsely flagged time | 12.933 s | 7.967 s |
| Missed turtling | 8.433 s | 8.433 s |
| Entirely negative runs flagged | 0 of 7 | 0 of 7 |

Run 1's remaining misses are 6661-6719 and 8101-8294. The gate addresses when turtling becomes eligible; it does not repair those interruptions. Runs 2 and 12 retain their earlier false time. The eight randomly selected source runs are unchanged; improvement occurs in one targeted cell. Earlier reviewed development examples retain their matches, including the 5606 onset and 7080-7439 continuous interval. The six new-source clips from the earlier seven-clip validation have not been re-evaluated here.

These are **development results using reviewed labels**, not independent validation. A movement prerequisite cannot establish posture, and a camera bump must never be treated as animal movement. Automatic camera-motion detection or stabilization has not been implemented.

## Evidence and review

Local evidence: `outputs/ba_turtling_recovery_gate_20261006/`. Firebird destination: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_recovery_gate_20261006`.

`USER_CLARIFICATION.json` records the corrected onset, death-feint protocol and camera attribution. `COMPARISON.json` records all 12 runs, prior-example regressions, hashes and the unchanged legacy wake results. Per-frame eligibility and uncertainty states are retained beside the gated candidates. Ten focused tests cover brief jumps, missing tracking, threshold boundaries, permanent camera offsets, reference reacquisition and unchanged input coordinates.

The new offline Run 1 page links the same frozen video to the human score, prior candidate and gated candidate, with controls below the arena. The earlier PDF and review package remain historical 0.2.0 comparisons. This experiment does not replace them or claim a newly validated posture measure.
