# Paired IDtracker comparison: 2024 six-beetle battles

Each source has two independent IDtracker runs. **Human + background** preserves its original threshold, blob area, start/end frames, and four ROIs while enabling background subtraction. **Shared 50/400** uses intensity 50–255, minimum area 400 px², and background subtraction, preserving that source's frame interval and ROIs. The source TOMLs were never overwritten.

Missingness and jumps below use original IDtracker coordinates on the full specified tracking interval [start, end); presumed social contact positions are not substituted. A present IDtracker coordinate is not necessarily a direct visual detection. Estimated accuracy is IDtracker's estimate, not human identity validation. No failed run is assigned a zero-missingness score.

| Source | Start–end (end exclusive) | Human intensity / min area | Human missing % | Shared missing % | Shared − human (pp) | Human estimated accuracy % | Shared estimated accuracy % | Human jumps >100 px | Shared jumps >100 px | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| groupagetrial01_062024_Box02_MIX | 422–16998 | 0–143 / 329.0 | 98.79 | 16.37 | -82.42 | 96.72 | 95.29 | 0 | 1 | both measurable |
| groupagetrial02_062024_Box01_YOUNG | 242–17048 | 43–255 / 228.0 | 15.52 | 20.13 | 4.61 | 94.23 | 94.13 | 5 | 8 | both measurable |
| groupagetrial02_062024_Box03_OLD | 484–17048 | 31–255 / 286.0 | 19.22 | 20.87 | 1.65 | 99.72 | 93.71 | 0 | 0 | both measurable |
| groupagetrial03_062124_Box03_OLD | 420–16410 | 32–255 / 171.0 | 24.31 | 28.39 | 4.08 | 99.10 | 99.81 | 1 | 0 | both measurable |
| groupagetrial04_062124_Box01_MIX | 175–16426 | 55–255 / 56.0 | 22.47 | 24.52 | 2.05 | 90.15 | 95.92 | 15 | 4 | both measurable |

Paired comparisons available: **5/5**.
Shared settings reduced missingness in **1/5** measurable pairs; median within-pair change was **+2.05 percentage points**. This is descriptive, not a test of biological significance.

The shared setting should be judged across missingness, estimated accuracy, per-beetle results, and jump counts. Neither setting has been manually reviewed for identity continuity or pile interactions. Estimated accuracy can be misleading when almost all coordinates are missing.

Firebird batch: `/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024/managed_idtracker_runs/paired_20260922_004953_utc`. Detailed run metrics are in `runs.csv`; pairwise differences are in `pairs.csv`, and individual-beetle missingness is in `per_beetle.csv`.
