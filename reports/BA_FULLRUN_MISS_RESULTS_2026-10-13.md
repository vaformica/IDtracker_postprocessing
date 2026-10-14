# A second substantial BA turtling miss

AI-written synthesis by Codex, 13 October 2026, from VAF's returned six-run scores. All six decisions are complete and the scoring-set fingerprint and frozen prediction hashes match. Original export preserved in `outputs/ba_fullrun_miss_results_20261013/` with reproducible import and `COMPARISON.json`.

Clip 3 is BA030. VAF marked on-back posture from 1547 through 8179 inclusive: 6,633 frames, or 221.1 seconds. Frozen 0.4 flags none. Every missed position is finite and recovery-eligible. Thus neither missing coordinates nor an unconfirmed recovery gate explains this miss. The interval reaches the window end; 8179 is not a confirmed righting endpoint, and the whole episode may be longer.

The other five runs have explicit no-turtling decisions. Four were random selections and the other was the second targeted quiet case. BA030 was selected for long unflagged quiet stretches, so one miss among these six is not a population failure-rate estimate. The random subset contains no positive episode and therefore cannot estimate sensitivity.

Over 43,200 displayed frames, the frozen binary mask comparison gives TP 0, FN 6,633, FP 0, TN 36,567. There are 214 tracking-missing frames elsewhere, retained separately as detector-unknown; these must not be interpreted as confident negative detector decisions. No new positive tracking gap occurs in BA030. Flailing remains unassessed. All frozen masks were empty by selection outcome, so this set does not establish false-positive performance on flagged runs.

BA060 is therefore not the only large missed event. Keep frozen 0.4 as a movement-based screening baseline, but do not use it alone for unattended turtling duration estimates. Next investigate BA030's candidate/anchor failure alongside BA060, keeping the five negative runs as controls. Compare visual posture and movement regimes without moving thresholds to the known label. The prior image model failed other positive examples and introduced false positives at its more permissive setting; it is not ready for promotion. Any new candidate method should then face a frozen, recording-held-out posture benchmark before dyadic testing.

No refit, source mutation, production release, or dyadic work was performed. Results are local; no Firebird upload asserted.
