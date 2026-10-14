# Experimental BA turtling candidate rules, 5 October 2026

Vince's corrected second-clip onset is global frame **5606**, continuing through the excerpt's last frame **6464**. This supersedes the full-clip interpretation. The first accepted onset is **6894**, through displayed frame **7463**. These are development labels; offsets after either clip remain unknown.

## Implemented rules

`ba_turtling_candidates.py` version `0.1.0-experimental` uses the frozen prototype looping mask as an anchor. No recording identifiers, annotated frame numbers, or human labels enter the detector. It preserves the original mask and adds explicitly identified candidate frames:

1. **Onset transition hypothesis.** Before an original candidate bout lasting at least 4 seconds, look backward at most 4 seconds for the latest observed centroid displacement greater than 20 and at most 200 original-image pixels. The landing frame through the first 4 seconds of the original bout must have complete observations, no further step above 20 pixels, and remain within 35 pixels of the anchor's median position. No onset expansion is allowed if another original candidate bout occurred in the lookback interval. The landing frame becomes the candidate onset. This transition may also be a segmentation/tracking artifact; it is not proof of an actual flip.
2. **Quiet-pause hypothesis.** Bridge at most 1 second between two ORIGINAL candidate bouts only if the gap and up to 1 second of context on either side are completely observed, contain no step above 20 pixels, and all remain within 35 pixels of their joint median. Added frames never serve as new anchors for recursive bridging.
3. **Unknown remains unknown.** Missing positions are not filled. Stationarity without loop anchors does not initiate an episode. Long pauses and trailing immobility are not automatically carried forward. No rule changes the raw coordinates, movement measurements, or attributed review labels.

The pixel thresholds reuse existing baseline/BA movement scales; the time limits are explicit provisional development choices. They have not been optimized or validated across cameras, body sizes, or independent source recordings. Both reviewed transitions have centroid displacements (26.4 and 45.4 px); their shared pattern motivated the onset hypothesis. This limited sample cannot establish whether that cue separates flips from tracking errors or ordinary stops.

## Development comparison

Compute baseline and experimental masks on all 7,200 frames of each of the three originally scored source windows, then extract review clips. The retrieved source TOML/trajectory hashes match the original selection key. Older broad clip labels are preserved, with later onset/posture feedback taking precedence in the evaluation label array. Overlapping annotations count once; unreviewed frames do not enter accuracy totals.

| Reviewed example | Prototype | Experimental | Vince's reviewed result |
| --- | --- | --- | --- |
| First clip | 6894-7463; 19.000 s | 6894-7463; 19.000 s | Same |
| Second clip | 5645-6071 and 6082-6464; 27.000 s | 5606-6464; 28.633 s | Same |

Across **7,200 unique reviewed frames** (2,629 positive, 4,571 negative), the prototype has 49 missed positive frames and zero false-positive frames under the latest labels. The experimental rule recovers all 49 and adds no false positives **within the reviewed frames**. This is a fit to development examples, not held-out validation or an estimate of general accuracy. Six originally positive clips are not six independent events.

Across the full 21,600 analyzed frames, the experimental mask adds **67** candidate frames: 39 at the reviewed onset, 10 in the reviewed quiet pause, and **18 unreviewed frames at 7251-7268 in Camera_2_40359705_20260629_1321_ACT1_C3**. The final interval needs visual scoring; do not count it as a confirmed improvement. The source with zero original candidates still has zero candidates. Onset/offset generalization and longer quiet overturned periods remain unresolved.

## Pipeline and review outputs

`run_ba_pipeline.py` version **0.2.1-ba** accepts `--experimental-turtling`. This is opt-in. Original summary metrics and `frame_data.csv` flags stay unchanged. Opt-in bundles add `turtling_experimental.json`, explicit version/rules/status in the manifest, a separate experimental PDF page, and a viewer checkbox to compare experimental candidates with the original detector. Added onset/pause frames appear purple; human-reviewed posture remains a separate layer. The default BA pipeline and all social PSC routes keep their previous detector behavior.

Local evidence and reproducible evaluation/build scripts: `outputs/ba_turtling_continuity_dev_20261005/`. The two new viewers use computed automatic candidates, without applying manual corrections. Downloads delivery: `/Users/New/Downloads/BA_turtling_experimental_20261005/START_HERE.html`. Firebird development root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_continuity_dev_v0_1_0_20261005`.

Validation: 20 targeted BA tests pass, including no standalone immobility episode, no missing/jump/long-gap bridging, no recursive onset filling across nearby bouts, bounded onset extension and baseline preservation. Viewer behavior checks cover frames before onset, onset, quiet pause, the baseline toggle and final duration. Both PDF pages were rendered and visually inspected. Embedded MP4 bytes match previously verified videos. No new full BA scientific release or all-BA batch has been run.

Next scientific checks: score the new 18-frame interval; evaluate independently selected full source recordings; label actual recoveries and prolonged quiet overturning so offset rules can be tested. Keep the rule experimental until those checks support promotion.
