# Dyadic posture clarification results — October 15, 2026

Vince's returned identity-specific review resolves the apparent contradiction: ID 0 is on its back in each marked interval; ID 1 is not. The export timestamp is October 16 at 00:05 UTC, which is October 15 in America/New_York.

| Clarification clip | Previous image clip | Inclusive global frames | ID 0 | ID 1 |
| --- | --- | --- | --- | --- |
| 1 | 1 | 7032–7179 | On back | Not turtling |
| 2 | 3 | 2720–3169 | On back | Not turtling |
| 3 | 5 | 5146–5595 | On back | Not turtling |

Clip 1's other 302 frames remain unmarked in this export, despite full viewing coverage. No onset or recovery outside the marked ranges is inferred. The first clip's former ID 1 positive attribution is superseded within 7032–7179 by this explicit per-ID clarification. No global reinterpretation of the earlier score files was performed.

The frozen image model still has real errors: in previous image clip 5 it flags ID 1 in 27 of 28 sampled images, although Vince confirms ID 1 is not on its back. It recognizes ID 0 in all 28 sampled images from previous clip 3. In the clarified first interval, available frozen samples for ID 1 include 12 false flags and 8 correct negatives; these include historical sampling grids and should not be equated with the 28-image-per-clip review grid. There are no stored frozen predictions for the newly confirmed positive ID 0 intervals in clips 1 and 5. Missing predictions are not missed detections or negative labels.

The model was developed with earlier identity-ambiguous annotations. Its historical metrics should not be used as validation of turtling accuracy. Preserve this diagnostic result, audit identity attribution in the remaining training positives, and use explicitly labeled per-beetle intervals for any future refit. Candidate flagging with human confirmation remains the appropriate current use. Observed partner separation may prioritize review but must never prohibit on-back posture near another beetle.

Original export, hash, attributed interval conversion, reproducible import script and diagnostic comparison are preserved in `outputs/dyadic_posture_clarification_results_20261015/`. All three case identities, bounds and source excerpt hashes match the reviewer manifest; interval bounds, allowed states, nonoverlap and case uniqueness passed validation. Source scores and frozen predictions remain unchanged. No detector retraining or production changes were made.
