# BA second-clip posture clarification, 5 October 2026

Vince clarified: "IT never turns over it is always turtled" after confirming the first example's timing. The second excerpt is already overturned at its first frame and remains overturned through its last frame. The previously mentioned 3-second point is not treated as the posture onset.

The separate attributed review now covers global frames **5505-6464 inclusive**, 960 frames at 30 fps = **32.000 seconds** confirmed overturned. Both clip boundaries are censored: neither the biological onset nor recovery is observed. Quiet intervals count toward overturned time. The prior specific inactive-flailing observation at 6072-6081 is retained; this does not provide a complete active/inactive-flailing segmentation.

The original movement flags remain unchanged at **810 frames / 27 seconds**. The earlier reviewed 27.333-second result and original scoring files are preserved. The first accepted offline review is copied byte-for-byte unchanged. No detector thresholds changed and no classifier has been newly validated.

`ba_turtling.py` 0.2.1 now labels fully reviewed windows accurately instead of always saying they contain unconfirmed automatic candidates. The reviewed PDF reports clipped boundaries, and the viewer distinguishes full-window posture review from partial review. Fourteen targeted BA tests pass, including whole-window overturned accounting across quiet frames with unchanged baseline flags. The new PDF was rendered and visually checked. Embedded movie bytes match the previously verified source video. New Safari playback was not verified because the browser was actively changing during another review session.

New local evidence: `outputs/ba_turtling_full_clip_review_20261005/`.
Durable offline handoff: `/Users/New/Downloads/BA_turtling_review_20261005/START_HERE.html`.
Separate Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_full_clip_review_v0_2_1_20261005`.
See `VERIFICATION.json` and the remote `FIREBIRD_VERIFICATION.json` for hashes, video frame count, and lab permissions. This is an attributed review of one excerpt, not approval of a full BA run or a new automatic release.

## Superseding correction: explicit onset frame 5606

Vince subsequently specified: "The beetle trutles at 5606 and stays that way for hte rest of the video." This supersedes the full-clip interpretation above. The current second-clip review labels frames 5505-5605 as before onset and **5606-6464 inclusive** as continuously overturned: **859 frames / 30 fps = 28.633333 seconds**, beginning 3.366667 seconds into the clip. Recovery is not visible; only the right boundary is censored. The prior quiet-pause observation remains within this interval. The first example is unchanged, and automatic candidate flags remain unchanged at 27 seconds.

Current local evidence: `outputs/ba_turtling_onset5606_review_20261005/`.
Current durable review: `/Users/New/Downloads/BA_turtling_review_20261005_onset5606/START_HERE.html`.
Current Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_onset5606_review_v0_2_1_20261005`.
The earlier interpretation and source files remain preserved. The new PDF was rendered and visually checked; accounting assertions verify the transition at 5605/5606, inclusive duration, unchanged candidate flags, and the right-censored endpoint. Embedded MP4 bytes and delivered copies were verified, and viewer JavaScript passes its syntax check. This correction changes attributed annotations only, not the automatic detector.
