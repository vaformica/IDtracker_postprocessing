# Withdrawn RAW/PSC review viewer v2

The 2024 GroupTrial viewer `raw-psc-compare-v2` correctly rotated and
letterboxed Box 3, but its rebuild path interpreted the analysis `window`
value as a number of observations. The analysis defines `window` as movement
intervals, so a window of W has W + 1 frame observations. Each of the 11 v2
review MP4s omitted the final analyzed frame. For example,
`groupagetrial01_062024_Box01_OLD_TEst` has frame-data observations at global
frames 220–16997 (16,778 frames), while the v2 review video has 16,777 frames.

The PSC 1.5.1 trajectory, CSV, and PDF analyses are unaffected. The v2
review videos and its 11-review ZIP are withdrawn; they must not be used for
frame-complete review. Viewer v3 includes the final source-video frame and
checks the encoded frame count against the analysis before publishing.
