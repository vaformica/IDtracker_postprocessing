# BA image-supported posture investigation across examples

AI-written by Codex, 12 October 2026. BA-only development evidence; not validated or promoted.

The broader examples show that this image model is not yet a reliable general posture detector. At the fixed 0.90 threshold it flags only 6 of 770 human-positive sampled instants in six other clips; at 0.75 it flags 209. Frozen 0.4 already covers those sampled positives. Images do recover 163 of BA060’s 495 missed sampled instants at 0.90 and 382 at 0.75, but the eleven wider-crop negative clips expose 13 new false flags in BA039 at 0.75. At 0.90 there are 0 new false flags in those negative clips, with substantial abstention. Keep this as experimental supplemental evidence.

Vince asked to avoid concentrating on one video. The completed extension therefore covers eleven human-negative clips and six other on-back/onset/righting clips with wider image context, in addition to the original 60-clip recording-held-out model comparisons and fresh/focused evaluation. BA060 is one failure case, never a training example.

| Image threshold | BA060 misses recovered | New false flags before BA060 flip | New false flags: 11 negative clips | New false flags: 6 other posture clips |
|---|---:|---:|---:|---:|
| 0.5 | 482 / 495 | 224 | 513 | 70 |
| 0.75 | 382 / 495 | 0 | 13 | 0 |
| 0.9 | 163 / 495 | 0 | 0 | 0 |
| 0.95 | 7 / 495 | 0 | 0 | 0 |

All counts are sampled instants, every six frames at 30 fps. Do not convert these to exact duration errors or present them as population accuracy. Threshold .90 was primary; .50/.75/.95 were predeclared comparisons, not post-hoc optimizations. The supplemental OR rule preserves all existing 0.4 suggestions, including its false positives.

## Other posture examples

| Case | Human-positive samples | Image usable / total | 0.4 positive hits | Image hits .90 | Image hits .75 | New false .90 | New false .75 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ba_016 | 100 | 96/100 | 100 | 0 | 67 | 0 | 0 |
| ba_026 | 72 | 114/131 | 72 | 6 | 28 | 0 | 0 |
| ba_051 | 100 | 100/100 | 100 | 0 | 32 | 0 | 0 |
| ba_058 | 344 | 344/344 | 344 | 0 | 0 | 0 | 0 |
| ba_069 | 86 | 60/100 | 86 | 0 | 22 | 0 | 0 |
| fresh_16 | 68 | 120/150 | 68 | 0 | 60 | 0 | 0 |

The negative check contains 2099 labeled sampled instants; 1405 have usable eligible image features and 694 remain unavailable/ineligible. The six other posture clips contain 925 sampled instants, with 834 usable. No flag on an unassessed image is evidence of upright posture. Abstention and recovery-ineligible coverage are retained; unassessed frames are never declared upright. Exact label revisions and source hashes are preserved. The widened negatives are an explicit correction to the initially inadequate crop coverage, not extra training data. BA039 exposes a false event at .75 that was hidden by the narrow crop's abstention.

## Interpretation

BA060 misses are not missing coordinates or a closed recovery gate: every fully contained 120-frame window in 3942–6909 fails the baseline path requirement (2,849 windows; median 17.86 px versus 120 px required). Most also fail turning. Relaxing centroid gates cannot establish posture and can reintroduce upright loops.

Images supply useful additional evidence, but strict-threshold suggestions are fragmented and image-only recall varies across other positive cases. Improve body isolation near walls/writing and temporal posture evidence across recordings; freeze a revised method before a new blind complete-run test. Do not use BA060-specific timing, simple back-extension or a selected threshold as a general correction. No dyadic test or production promotion was made.

## Reproducibility and verification

The model is ExtraTrees (240 trees, depth 12, leaf minimum 8, balanced classes, seed 20261012), using appearance plus image-change descriptors. Model input contains no absolute coordinates, frame/run IDs, human labels or centroid-motion features. Entire target recordings are excluded from training. Original held-out predictions were reproduced for the expanded-image checks. Existing human scores already informed previous detector development, so these remain selected challenge comparisons, not prospective independent validation.

Initial checks independently reconstruct persistence and counts; 98 available local input files match remote input hashes. BA060's original source hash matches frozen provenance. Expanded media retain decoded counts and scored-video alignment checks. Other expanded sources have size/mtime comparisons to their previously hashed metadata, not fresh full-source hashes. Wider image context does not prove valid beetle segmentation or biological posture. Flailing remains unassessed.

Evidence root: `outputs/ba_posture_image_investigation_20261012/` locally and `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_posture_image_investigation_20261012/` on Firebird. Open [the visual comparison](../outputs/ba_posture_image_investigation_20261012/START_HERE.html). See `RESULTS.json`, `negative_context_check/RESULTS.json`, `other_posture_examples/RESULTS.json`, `VERIFICATION.json` and `BROADER_VERIFICATION.json`. Initial failed executions and the first crop attempt are retained. All new Firebird folders use lab-group permissions; production and original inputs remain unchanged.
