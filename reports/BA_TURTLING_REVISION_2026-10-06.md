# BA turtling revision: lower-motion episodes

Current follow-up: [death-feint recovery gate experiment](BA_TURTLING_RECOVERY_GATE_2026-10-06.md) removes Run 1's early false event. The 0.2.0 results below remain the preserved pre-gate comparison.

The 12 full-run scores showed that the detector often lost an overturned beetle while it was still flailing. The main cause was the requirement for at least 120 pixels of centroid movement in each four-second window. The new **0.2.0-development** experiment reduces that requirement within regions supported by an original candidate. It substantially improves the fit to these scores, but does not yet establish posture from video or justify processing all BA runs as validated turtling measurements.

The original processor and `ba_turtling_candidates.py` 0.1.0 remain unchanged. The separate experiment is in `ba_turtling_episode_experiment.py`; `ba_turtling_diagnostics.py` explains the original detector's gates. No production integration or official release has occurred.

## What changed and why

The diagnostic audit reproduced the frozen baseline exactly for all 12 runs. Removing only the path-length gate recovered 2,445 missed frames in Run 1 and 67 in Run 6 without adding false positives in this set. Removing the radius gate, by contrast, produced many false candidates, including in negative runs. These ablations explain the failure; they are not proposed detector settings.

The revision retains all the original finite-position, step, radius, turning and straightness checks. It allows a 60-pixel path in a connected region only if that region includes an original 120-pixel-path candidate. This halves the movement requirement without letting weaker evidence independently establish an event. Exploratory Run 1 path thresholds of 120, 100, 80, 60, 40, 20 and 0 pixels were inspected; 60 is a development choice, not a biologically validated threshold.

The onset extension now rejects steps over 100 pixels. Run 1's former extension was triggered by a 142.7-pixel step, adding 68 false frames. The earlier reviewed 5606 onset had a 45.4-pixel step and is preserved. The new cap is a heuristic to test further, not evidence that smaller jumps necessarily indicate flipping.

At the observation boundary, the revision permits up to one second of continuation after at least four seconds of support, provided positions are complete, steps stay at or below 20 pixels, and the last second of supporting positions plus the tail remain within 35 pixels of their shared median. The result is explicitly a right-censored continuation hypothesis. The existing one-second bounded-gap rule is retained; long gaps are not automatically filled.

## Results against VAF's scores

All times below are seconds. The comparison is to the previously evaluated 0.1.0 experimental detector.

| Run | Human on-back time | Previous missed | Revised missed | Previous extra | Revised extra |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 182.033 | 86.167 | 8.433 | 7.233 | 4.967 |
| 2 | 73.433 | 0 | 0 | 1.733 | 1.733 |
| 6 | 188.400 | 1.900 | 0 | 0 | 0 |
| 8 | 93.000 | 0 | 0 | 0 | 0 |
| 12 | 92.533 | 0 | 0 | 6.233 | 6.233 |

Runs 3, 4, 5, 7, 9, 10 and 11 remain unflagged, matching VAF's explicit confirmation that all seven had neither turtling nor flailing. Across the 12 runs, missed time falls from 88.067 to 8.433 seconds; falsely flagged time falls from 15.200 to 12.933 seconds. The eight randomly selected source runs are unchanged. The improvement occurs in the four targeted cells that share recordings with the random sample.

The earlier three-source development comparison retains zero errors across its 7,200 previously reviewed frames. Explicit checks also preserve the 5606-6464 continuous event and the later reviewed 7080-7439 interval. Unlabeled portions of those recordings are excluded from accuracy counts. The six new-source clips in the earlier seven-clip validation were not re-evaluated in this revision.

**These are development results.** The 12 full runs informed the rule changes, so they no longer provide an independent test of the new version. Eight source recordings and four additional targeted cells are not 12 independent recordings. Frame counts also are not independent biological replicates.

## Remaining errors and the next useful review

Run 1's baseline false event at global frames **1177-1325** remains. The removed extension was false, but reducing it does not solve the original false event. The revision now starts the real event at **2834**, matching the human onset. It still misses **6661-6719** and **8101-8294**. A weaker-motion region at the end lacks a connected original anchor and is deliberately left unflagged. Run 6 now matches the human interval **2591-8242**, including its observed quiet-on-back interval and the final frames. Runs 2 and 12 retain their earlier false time.

No new broad scoring round is needed yet. First inspect the remaining Run 1 errors, especially whether image appearance can distinguish its early false event from overturned posture. Simply lengthening every gap would hide rather than resolve that ambiguity. A later independent set is needed before promoting a frozen revision.

## Review and reproducibility

Local evidence: `outputs/ba_turtling_diagnostics_20261006/`. Firebird: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_diagnostics_20261006`.

The `review/` folder contains two complete comparison MP4s, an offline `START_HERE.html` with controls below the video, and a two-page PDF. Human scores and the two candidate versions appear above the arena. The video bytes recovered from the previously delivered scorer match the frozen input MP4 hashes. Each new MP4 is H.264, 30 fps, 7,200 encoded frames. The PDF's rendered pages and selected encoded video frames were visually inspected. Browser playback itself was not tool-tested.

`GATE_AUDIT.json`, per-run feature arrays, `REVISION_COMPARISON.json`, per-frame prediction files, code snapshots, and checksums preserve the scientific and software distinctions. Diagnostic Slurm job **916629** completed with exit code 0. Eleven focused software tests passed; the real-input comparison reproduced the original baseline and checked unchanged coordinates, missing-frame handling, seven negative runs, and the earlier reviewed events. This is regression evidence, not biological validation.

The repository currently reports a damaged Git pack and `bad object HEAD`. This task preserves its files without attempting Git repair, committing, or publishing.
