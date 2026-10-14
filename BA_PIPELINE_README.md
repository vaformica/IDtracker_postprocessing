# BA single-animal pipeline

BA uses one animal, one arena ROI, and **7,200 inclusive observations** from the source TOML's tracking start (`end = start + 7199`). `run_ba_pipeline.py` version `0.1.0-ba` calls the existing `processor.py` version `0.8.1` BA calculations and PDF renderer. It does not run the social PSC model. Dyadic and group processing remain separate.

```bash
python run_ba_pipeline.py --toml /source/BA_A1.toml \
  --session /source/session_BA_A1 --output /new/versioned/output/BA_A1
```

The script validates single-animal geometry, source/session ROI agreement, video basename, and tracking-window coverage. It refuses an existing output directory, verifies source hashes before/after processing, and publishes a complete staged directory. Use the matching original full-length video and global-frame trajectories, not a cropped or interval-relative input. `--source-video` allows an independently verified local copy retaining the original basename.

## Retained scientific rules

- Original coordinates stay unchanged; missing positions are not interpolated.
- Adjacent steps over 200 pixels are excluded from movement and plotted connections. Endpoint locations remain eligible for per-frame ROI counts.
- Movement/wake threshold: 30 pixels. Wall buffer: 30 pixels. These are configurable and recorded.
- The BA focal animal anchors its post-wake analyses, including the existing 3,600-interval comparison only when a complete window fits.
- Turtling candidates retain the prototype's movement-pattern rule; these are not proof of posture or a general immobility classifier.
- PDF layout is the prototype BA layout. Video crop preserves aspect and original orientation. No fungus or social inference is introduced. Historical summary columns may remain present as not applicable.

## Each run contains

`summary.csv`, `frame_data.csv`, the TOML-named PDF, `review.html`, `review_video.mp4`, `qc.json`, `source.toml`, and `manifest.json`. Keep HTML and MP4 together. The viewer exports attributed notes separately and does not silently edit automatic coordinates or approve a run. All results start **UNREVIEWED**.

Frame data uses zero-based `animal_id=0`, original global frames, x/y in pixels, known-location and arena/wall/interior indicators, accepted adjacent steps and distances, rejected-jump flags, and turtling candidates. The first frame has no within-window incoming step. Blank distance means no accepted step, not zero motion. The summary retains the prototype's original column definitions in `DATA_DICTIONARY.md`.

## Pilot and QC

`ba_inventory.py` performs read-only source/session matching by video basename and exact arena polygon, recording source hashes and segmentation-setting differences. A match is a reproducible selection aid, not proof of tracking quality. The default seed is `20260929`: sample six source videos uniformly, then one TOML per selected video uniformly, **before excluding QC failures**. This is video-stratified sampling, not a simple random sample of all TOMLs.

`ba_pilot_batch.py` retains blocked selections and runs only uniquely matched configurations without inventory flags. Source/session hashes are checked again. Completed folders and their ZIPs are hash-verified. The release receipt distinguishes completed, blocked, and failed selections.

Initial `ba-qc-pilot-v1` flags are **review prompts, not automatic exclusions**:

| Metric | Provisional flag |
| --- | --- |
| Missing fraction | >5% of analysis frames |
| Longest missing episode | >120 frames |
| Rejected jump fraction | >1% of adjacent pairs with both coordinates |
| Outside-arena fraction | >1% of known positions |
| Consecutive identical positions | >600 frame observations |
| Missing baseline or no reliable wake | Explicit review flag |

Stationarity and absent wake can reflect real behavior. A trajectory problem does not establish a defective video. Video-level summaries should preserve both the number assessed and the number flagged; the pilot has only one selected arena per video. Codec/decode completion is checked by MP4 generation and exact encoded-frame count; visual problems such as glare or washout still need video inspection. Review flagged episodes before setting final QC thresholds or rejecting trials.

## Firebird pilot

New root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_2026_7200frames_pilot_v0_1_0_20260929`.

Top level contains source inventory, selection/status records, QC index, release receipt, code snapshot, logs, `runs/`, and `individual_run_zips/`. Prior BA analyses and source data remain untouched. This pilot reprocesses existing IDtracker coordinates; it does not rerun IDtracker or establish that historical tracking used every current TOML setting.

## Turtling bout development (0.2.0-ba, October 1)

`ba_turtling.py` converts the unchanged baseline frame mask into inclusive bouts,
seconds, percentage of detected time, longest bout, and unknown tracking time.
Missing frames split bouts; no temporal smoothing or posture inference is added.
`turtling_bouts.json` is the shared accounting record for viewer v2 and the appended
PDF bout pages. The synchronized HTML video overlay shows current candidate state
and accumulated candidate seconds; the underlying MP4 remains an unannotated crop.

The viewer exports attributed confirmed-overturned, rejected-overturned,
active-flailing, uncertain, and note-only ranges separately. Confirmed overturned
intervals include quiet pauses. `ba_turtling.summarize_review` computes reviewed
coverage separately, deduplicates overlapping identical decisions, and rejects
conflicting posture decisions. Unreviewed intervals never become confirmed upright.
Exports do not automatically alter the scientific bundle or its PDF.

This is a development integration of the existing candidate detector, not a newly
validated posture classifier. Longer transition excerpts are under
`outputs/ba_turtling_development_20261001/`; no historical releases are replaced.

### Reviewed quiet pauses (module 0.2.0)

A confirmed quiet overturned interval now joins the separate review-assisted
posture episode mask. Raw movement candidate flags remain unchanged. There is no
automatic short-gap filling: other gaps remain unresolved until reviewed.
Viewer decisions can explicitly mark flailing inactive while posture remains
confirmed overturned. `apply_ba_turtling_review.py` writes both the original
candidate account and the review-assisted episode account, plus per-frame evidence.
The original fields and v0.2 development artifacts remain historical.

## Full-clip posture clarification (2026-10-05)

Vince corrected the second calibration excerpt onset to global frame 5606. Frames 5606-6464 inclusive count as continuously overturned (28.633 seconds), including quiet periods; recovery is not visible. This supersedes the earlier full-clip 32-second interpretation. The first example's timing remains accepted. Module 0.2.1 correctly labels full-window human posture review in the JSON, viewer, and PDF; automatic candidate flags remain unchanged. See [the attributed review and delivery record](reports/BA_TURTLING_FULL_CLIP_REVIEW_2026-10-05.md).

## Experimental automatic continuity rules (2026-10-05)

Pipeline 0.2.1-ba adds opt-in `--experimental-turtling`: separate onset-transition and short quiet-pause candidates, an additional PDF page, and a video-viewer comparison checkbox. Baseline metrics stay unchanged. The revised rule recovers onset 5606 and the reviewed quiet pause while retaining the first clip's onset 6894. It also adds an unreviewed 18-frame interval elsewhere; independent validation is pending. See [rules, comparison and limitations](reports/BA_TURTLING_CONTINUITY_RULES_2026-10-05.md).

## Human trace QC before inclusion decisions

The additional-100 BA collection now has a separate trace-first human screening
page with issue buttons, short/full video playback, and attributed exclusion
recommendations. See [the human QC workflow](reports/BA_HUMAN_QC_2026-10-13.md).
Start with a quick trace skim; inspect video as needed and export the QC JSON.
A skim is not full biological approval, and exclusion recommendations do not
silently remove data or alter analysis denominators. This local development
step does not replace original posture scores or the recovery-review queue.
