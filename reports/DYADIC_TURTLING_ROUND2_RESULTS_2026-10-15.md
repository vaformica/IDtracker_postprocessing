# Dyadic posture round-two results — October 15, 2026

VAF's returned six-clip review shows that grappling/fighting can resemble the trajectory signatures used by the turtling screen. It also demonstrates false candidates outside the interaction-ambiguous state and a missed on-back episode. Development version 0.1.0 is not ready to supply automatic turtling durations.

The original JSON is preserved byte-for-byte in `outputs/dyadic_turtling_round2_results_20261015/scores_VAF_original.json`. `COMPARISON.json` records its hash, all six verified run/identity/frame/source-video matches, interval validation, and comparison with frozen predictions. No code, source tracking, earlier scores, or active review page was changed by this import.

## What the scores show

| Round-two clip | VAF evidence | Frozen development result |
| --- | --- | --- |
| 1 | On back 3143–3260; not turtling 3261–3427; grappling note | All 118 positive frames are quiet candidates. Of 167 negative frames, 35 remain quiet candidates and 132 are interaction ambiguous. Remaining 315 frames are unscored. |
| 2 | Fighting, not turtling, all 600 frames | 594 interaction ambiguous; six tracking unknown. Underlying loop screen flags all 594 observed frames. These are abstentions, not automatic turtling positives. |
| 3 | Whole-clip overall assessment: not turtling; viewed checked; no marked intervals | All 600 frames are quiet candidates. Strong qualitative false-alarm evidence, but no explicit frame-level negative labels are fabricated. |
| 4 | Fighting, not turtling, all 600 frames | 518 interaction ambiguous; 82 no candidate. Underlying quiet screen flags those 518 frames. |
| 5 | Explicit not-turtling interval covering all 600 frames | 351 quiet and 49 loop candidate frames; 42 interaction ambiguous, 38 tracking unknown, 120 no candidate. Full-viewed checkbox is false; preserve this metadata discrepancy alongside the explicit interval. |
| 6 | On back 7032–7179, 148 frames | All 148 positive frames missed: neither loop nor quiet screen triggers. Other 452 frames remain unscored. |

Round two contains 266 explicitly positive and 1,967 explicitly negative frames, with 1,367 frames unscored. The candidate states cover 118 positives and miss 148. Of explicitly negative frames, 435 are individual candidates, 1,286 interaction ambiguous, 44 tracking unknown and 202 no candidate. Abstentions are not true negatives. These selected clips include development follow-ups and cannot supply population error rates. The 113 positive frames at 3143–3255 in clip 1 overlap the first review; do not double-count them when combining rounds. Its newly marked positive extension through 3260 does not contradict the earlier unscored endpoint.

## Interpretation and next step

Two different behaviors can generate these features: fighting can move a centroid in small loops, while both a quiet overturned beetle and a quiet upright beetle can remain localized. The current evidence does not establish that every quiet false candidate is fighting; only attribute fighting to the clips with VAF's note. A near/missing partner gate helps abstain during interactions but cannot establish posture or safely rule out an overturned animal being grappled.

Do not widen stillness thresholds or label every quiet interval turtling. Do not suppress every close interaction as not turtling. Keep posture (on back / not on back / unknown) separate from social interaction (grappling/fighting or unknown); both may occur together. Candidate flags should remain review aids. The next defensible experiment needs image-supported posture evidence using the confirmed quiet positive, the quiet negative examples, the fighting examples, and the missed clip-6 positive. Use temporal source-resolution crops and held-out recordings before claiming a posture classifier. Until then, retain manual posture intervals and explicit unknowns for quantitative outcomes.

No detector fit, new video set, production promotion, or six-beetle work was triggered by this score import.
