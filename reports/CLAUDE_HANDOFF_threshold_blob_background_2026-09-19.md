# IDtracker.ai automation handoff: 2024 six-beetle battles

Prepared for Vince and Claude • 19 September 2026

**Dataset scope: six-beetle battles recorded in 2024.** This report concerns background subtraction, intensity thresholds, and minimum blob area for those recordings. The sweep used the 2024 groupage trial video `groupagetrial01_062024.mp4` and its OLD, OLD_TEst, and MIX configurations. These recommendations have not been validated for other years, animal counts, or recording setups.

## Recommendation

**Use background subtraction as the default for the automated workflow, and tune the intensity threshold and minimum blob area together in that mode.** Preserve human-entered TOMLs as comparison baselines. The experiment supports this default for these recordings, but does not prove that background subtraction wins on every video or that one threshold/area combination is universally optimal.

For a new recording with comparable image scale and acquisition conditions, a reasonable initial search center is:

```toml
use_bkg = true
intensity_ths = [50, 255]
area_ths = [400.0, inf]
```

This is a **provisional initialization**, not a validated replacement for the original settings. Here, “medium blob size” means a minimum accepted blob area of 400 pixels²; it is not a target size or an upper area limit. The background-on threshold range starts at 50 and ends at 255. The maximum blob area was unbounded in this experiment.

For existing OLD data, retain the original background-on setting of intensity **51–255** and minimum area **562 pixels²** as the baseline. It performed better than both shared settings discussed below. Do not silently overwrite existing TOMLs.

## What was tested

- Three source configurations: `groupagetrial01_062024_Box01_OLD.toml`, `groupagetrial01_062024_Box01_OLD_TEst.toml`, and `groupagetrial01_062024_Box02_MIX.toml`.
- Six animals per configuration. The first ROI is the arena; the next three are fungus ROIs, ordered left to right according to the established input convention.
- OLD and OLD_TEst describe the **same biological group**, with different source settings/ROI geometry. They are not independent biological replicates.
- Six controls retained each configuration's original threshold and area while toggling background subtraction.
- Fifty-four shared-grid runs: three configurations × two background modes × three intensity thresholds × three minimum areas.
- Background ON: intensity ranges **30–255, 50–255, 70–255**.
- Background OFF: intensity ranges **0–123, 0–143, 0–163**.
- Minimum areas: **250, 400, 550 pixels²**; maximum area unbounded.
- Standardized tracking interval: `[422, 16998)`; evaluation: **frames 422–7,622 inclusive**, or 7,201 frames and 43,206 animal-coordinate opportunities per run.
- **59 of 60 runs completed.** OLD_TEst with background OFF and its original 50–255 threshold failed to produce usable individual fragments. Treat that outcome as failed, not zero missingness.
- Installed IDtracker.ai version: **6.0.10**. The environment directory's name contains `6_0_14`; that name is not the installed version.

The comparisons below use standardized reruns of the human settings, not the original reports with different evaluation windows. Runs were not replicated across random seeds; small differences may include stochastic variation.

## Original human settings versus shared alternatives

| Source | Original background | Original intensity | Original minimum area, px² |
|---|---|---|---:|
| OLD | ON | 51–255 | 562 |
| OLD_TEst | ON | 50–255 | 361 |
| MIX | OFF | 0–143 | 329 |

“Shared winner” below means the shared-grid condition with the lowest weighted missing-coordinate rate: background ON, intensity 30–255, minimum area 400 pixels². “Medium” means background ON, intensity 50–255, minimum area 400 pixels².

| Source | Human settings: missing % | Shared winner: missing % | Medium: missing % |
|---|---:|---:|---:|
| OLD | **9.07** | 9.35 | 10.85 |
| OLD_TEst | 9.08 | **7.09** | 9.29 |
| MIX | **2.85** | 3.25 | 3.04 |
| Weighted comparison | 5.96 | **5.73** | 6.55 |

Weighting is OLD 25%, OLD_TEst 25%, and MIX 50%, to avoid counting the OLD biological group twice at full weight. This weighting is descriptive, not an inferential statistical test.

| Source | Human settings: estimated identity accuracy % | Shared winner: estimated identity accuracy % | Medium: estimated identity accuracy % |
|---|---:|---:|---:|
| OLD | 99.76 | 99.51 | 99.41 |
| OLD_TEst | 99.48 | 94.13 | 98.89 |
| MIX | 97.17 | 98.91 | 95.91 |

These accuracy values are **IDtracker estimates, not manual identity validation**. The shared winner's gain in OLD_TEst completeness coincides with a substantial drop in estimated identity accuracy. Its weighted missingness advantage over human settings is only **0.23 percentage points**. The medium setting did not improve missingness over the human settings in any of the three configurations.

**Conclusion:** the sweep identifies useful shared candidates but does not justify replacing the human settings as a blanket upgrade. Earlier enthusiasm for the medium setting should be understood as a proposal for initialization, not evidence that it outperformed the human TOMLs.

## Why background subtraction should be the default

Across the shared grid, the lowest estimated identity accuracy among the three configurations for each background-ON setting ranged from **94.13% to 97.65%**. For background-OFF settings, these minima ranged from **18.45% to 78.53%**. Some background-OFF settings produced few missing coordinates while having weak estimated identity accuracy. Completeness alone therefore gives a misleading impression of quality.

The same-threshold controls also show that background mode and threshold must be treated together:

- OLD at 51–255/minimum 562: **9.07% missing with background ON**, versus **83.33% OFF**.
- MIX at 0–143/minimum 329: **2.85% missing OFF**, versus approximately **99.00% ON**.

The MIX control is an important qualification: **do not simply turn background subtraction on while retaining a threshold intended for the non-subtracted image.** The successful background-on grid used a different intensity range. Its recommendation is for a jointly tuned pipeline, not an isolated switch.

MIX's original background-OFF settings remain a valid baseline: they had lower missingness than either shared background-ON candidate, although the 30–255/400 background-ON candidate had a higher estimated identity score. Thus, the default recommendation is supported by robustness across this grid, not universal superiority in every comparison.

## Guidance for Claude's automated project

1. Start with `use_bkg = true` for comparable new recordings. Keep an existing human TOML as a named, immutable baseline candidate.
2. Jointly explore threshold and minimum area. The tested background-on grid—lower threshold 30/50/70 and minimum area 250/400/550—is an evidence-based initial search space at this image scale. Include the exact human values when available. No finer-grid optimum has yet been established.
3. Do not transfer pixel-area values blindly to differently scaled images. Record image dimensions and resolution reduction; verify the installed version's area semantics before adapting values. These source trajectories use a 4096 × 2168 image coordinate system with resolution reduction 1.
4. Do not select the winner solely by lowest missingness. Compare estimated identity accuracy, per-animal missingness, all-six-present frames, abrupt jumps, segmentation/blob diagnostics, and visual identity continuity during contact and separation. Do not invent an automatic acceptance cutoff from this small experiment.
5. Inspect native IDtracker overlay video for shortlisted conditions at matched frame ranges, including contact, separation, stationary beetles on fungi, and arena edges. Repeat finalist runs if small differences drive selection; use additional biological recordings before declaring a general default.
6. Keep tracking quality separate from presumed social disappearance. Evaluate tracking missingness on the original trajectory output, before postprocessing inference. Report inferred positions separately. Original IDtracker output may itself contain gap filling, so a present coordinate is not proof of direct visual detection.
7. An unresolved disappearance is not automatically tracker failure. The current postprocessor requires a unique visible anchor within 60 pixels at disappearance; two possible anchors leave the position unresolved. For example, OLD ID 0 is absent during frames 6,482–7,125 after proximity to both IDs 3 and 4. This is a contact-related review candidate with ambiguous location, not demonstrated isolated tracking failure.
8. Preserve provenance: source TOML, generated TOML, source video/session identifiers, actual installed version, trajectory hashes, frame intervals, random seed when available, output metrics, and visual review status. Keep all temporal scientific summaries in **frames**.
9. Serialize area bounds as floats, for example `[400.0, inf]`. The installed legacy TOML reader rejected mixed integer/float arrays such as `[400, inf]` in the first submission. Verify generated configurations with the same parser used by the deployed IDtracker environment.
10. Verify genuine run completion from saved trajectories and completion evidence. In this environment successful tracking sometimes returned exit code 1; exit code alone was not a reliable outcome classifier.

## Evidence and reproducibility

This report is grounded in the completed sweep exports:

- [All run metrics and provenance](../results/firebird_grid_completed/comparison/all_runs.csv)
- [Shared-condition consensus table](../results/firebird_grid_completed/comparison/consensus.csv)
- [Four-page comparison PDF](../results/firebird_grid_completed/comparison/grid_comparison.pdf)
- [Full OLD disappearance audit](../results/OLD_disappearance_audit/disappearances.csv)

Remote sweep root:

`/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024/six_beetle_grid_20260918_v2`

Local source files live in the `IDtracker_postprocessing_prototype` repository. The postprocessor is `six_beetle_processor.py`, version `0.4.2-six-beetle`, based on the original processor version `0.8.1`.

This report recommends a starting strategy. It does not label the sweep candidates as visually validated or establish a universally optimal threshold, blob area, or background mode.
