# 2024 six-beetle GroupTrial: paired IDtracker settings

**Result, 22 September 2026.** All 10 Firebird jobs (898259-898268) produced six-beetle trajectories. They form five matched pairs: each source's human-entered intensity/area settings with background subtraction enabled, versus the provisional shared 50-255 intensity and 400.0 px² minimum area with background subtraction enabled. Each pair used the same original start and end frames, video, arena ROI, and three fungus ROIs. Source TOMLs were not overwritten. The submitted TOML hashes and ROI/frame equality were checked after completion.

| Source | Start frame | Human intensity / minimum area | Human missing % | Shared missing % | Shared minus human, pp | Human / shared estimated ID accuracy % | Raw jumps >100 px, human / shared |
|---|---:|---|---:|---:|---:|---:|---:|
| Trial 01 Box02 MIX | 422 | 0-143 / 329 | 98.79 | 16.37 | -82.42 | 96.72 / 95.29 | 0 / 1 |
| Trial 02 Box01 YOUNG | 242 | 43-255 / 228 | 15.52 | 20.13 | +4.61 | 94.23 / 94.13 | 5 / 8 |
| Trial 02 Box03 OLD | 484 | 31-255 / 286 | 19.22 | 20.87 | +1.65 | 99.72 / 93.71 | 0 / 0 |
| Trial 03 Box03 OLD | 420 | 32-255 / 171 | 24.31 | 28.39 | +4.08 | 99.10 / 99.81 | 1 / 0 |
| Trial 04 Box01 MIX | 175 | 55-255 / 56 | 22.47 | 24.52 | +2.05 | 90.15 / 95.92 | 15 / 4 |

The shared condition reduced missingness in **one of five** pairs. That pair is Trial 01 MIX, whose source TOML originally used **background subtraction off** with intensity 0-143. Turning background subtraction on without jointly retuning that intensity produced 98.79% missing coordinates and zero frames with all six beetles present. The shared condition rescued that control to 16.37% missing and 45.89% all-six-present frames. IDtracker's 96.72% estimated accuracy for the nearly empty control is not a meaningful endorsement of its identity quality.

For the **four source TOMLs already configured with background subtraction on**, their individual human settings had fewer missing coordinates in every pair. The shared setting increased missingness by 1.65-4.61 percentage points and decreased the proportion of all-six-present frames in all four. Estimated accuracy and >100-pixel jumps moved in different directions across pairs, so the shared setting is not a blanket improvement. These identity estimates are produced by IDtracker, not by manual verification. No identity continuity, fight, or presumed-social-contact overlay was visually reviewed for this comparison.

Missingness was computed from the raw saved six-animal `(frames, 6, 2)` trajectories over each source's full `[start, end)` interval: a beetle-frame is present only if both x and y are finite. The jump count is the number of adjacent assigned raw coordinate pairs separated by more than 100 pixels. Neither metric substitutes pile-model positions. A saved coordinate may reflect IDtracker gap filling and is not proof of direct visual detection. The five sources have different biological groups and start frames; this is a descriptive paired settings comparison, not an inferential test.

Detailed outputs: [two-page PDF](../output/pdf/GroupTrial_2024_paired_IDtracker_comparison.pdf), [run metrics](../results/paired_20260922_004953_utc/runs.csv), [paired differences](../results/paired_20260922_004953_utc/pairs.csv), and [per-beetle missingness](../results/paired_20260922_004953_utc/per_beetle.csv). These small final artifacts and the submission receipts are tracked with the repository; the original trajectories remain on Firebird under `/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024/managed_idtracker_runs/paired_20260922_004953_utc`.

The submission GUI bug found during this work was separate from the segmentation app: the GUI's background checkbox did not follow the newly selected TOML, and raw editor changes were staged automatically. Both are fixed. Future submitted receipts record the edit origin. The older failed Trial 01 MIX submissions contained `[329, inf]`, which IDtracker's parser rejected as a mixed integer/float area array; this batch used valid `[329.0, inf]` and `[400.0, inf]` bounds.
