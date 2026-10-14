# First human-scored BA turtling comparison — October 1, 2026

All 18 clips were scored. Vince labeled six clips overturned and actively flailing throughout all 12 seconds: 01, 09, 10, 12, 14, and 16. The other 12 clips were labeled no for both behaviors. The original reviewer field is blank; attribution to Vince comes from the upload in this chat, not from altering the submitted JSON.

## Frozen baseline result

Using any candidate frame as a positive clip: 6 true-positive clips, 1 false-positive clip, 11 true-negative clips, and 0 wholly missed positive clips. The baseline detected all six positive clips.

At frame level, labels cover each complete clip: 2150 true-positive frames, 30 false-positive frames, 4290 true-negative frames, and 10 missed frames. Within this selected sample, frame precision is 98.62% and recall is 99.54%. Human-positive duration is 72.000 seconds; baseline-positive duration is 72.667 seconds. The small net duration difference conceals both errors.

- Clip 07: human negative, but 30 baseline-positive frames (1 second).
- Clip 12: human positive throughout, but 10 frames missed (0.333 seconds).
- All other clips agree at every frame under the supplied full-clip labels.

Clip 07 ends at source frame 6923 and positive clip 01 starts at 6924 in the same recording. This makes onset overextension a plausible explanation for the false alarm, but the aggregate counts do not establish where its 30 positive frames occur. Inspect the contiguous transition and actual baseline mask before assigning a mechanism.

## Interpretation and next revision

These are development results, not held-out accuracy: only three source recordings were sampled, passages were enriched using baseline predictions, and positive clips may be pieces of the same prolonged event. Do not treat six positive clips as six independent events. The random-control selection was not restricted to baseline negatives; clip 12 was randomly selected and is positive.

The exploratory ranking score separates these labeled clips (maximum negative about 0.344; minimum positive about 4.953), but choosing a threshold in this gap would be fitting the same sample. It is not evidence of generalization and is not a reason to replace the baseline.

Prioritize event boundaries over globally loosening or tightening the detector. Next collect longer, contiguous footage spanning clip 07 into clip 01 and around clip 12, with exact posture/flailing onset and offset labels. Then test any proposed change on additional source videos withheld from threshold selection. Maintain separate posture and flailing labels; these examples provide no labeled quiet-overturned cases.

No shared detector parameters or prior releases were changed. Original submitted scores and hashes are preserved separately from this derived comparison. Clip hashes were checked against the original selection key.
