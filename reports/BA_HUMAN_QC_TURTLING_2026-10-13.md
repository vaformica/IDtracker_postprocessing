# Turtling flags in BA human QC

The viewer now applies frozen 0.4 development rules (baseline, episode 0.2,
recovery gate 0.1, continuity 0.3, boundary 0.4) to the separate strict proposal
track. This is a new screening application, not historical frozen predictions
on original tracking or biological validation. No thresholds were fitted.
Nine jump-blocked runs are NOT ASSESSED. Missing observations and unestablished
initial recovery also remain not assessed. Other observations distinguish
candidate detected from no candidate detected, which is not an upright label.

Purple trace, video circle/trail and timeline show automatic candidates. Pink
shows separately attributed possible-turtling intervals entered using Mark
turtling start/end. These intervals set the possible-turtling issue category,
remain in browser drafts, and export in JSON and summary CSV. Save Needs closer
review to commit a decision; open intervals must be completed or cleared.
Original generic issue ranges remain separate. Human flags do not retrain or
rewrite predictions and do not establish assessed coverage outside their ranges.

NEW_018 is flagged 6453–8294 inclusive, including the user's frame 8060.
Source-aligned 7200-frame masks for all 100 runs passed checks. Nine UI checks
include saving a typed turtling interval; ten schema/export checks pass.
Browser inspection verified purple trace and video overlay at NEW_018 frame 8060.

Reproduce with build_ba_qc_turtling.py. Input hashes and code hashes accompany
outputs/ba_human_qc_20261013/turtling_v1/. Original tracks, old scores and production
outputs remain unchanged. Jump-script troubleshooting remains paused.
