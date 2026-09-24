# PSC model 1.3.0 preview on Box 2 OLD (2024)

This is a local replay of the raw IDtracker trajectory and the same exported
blob detections used for the earlier model 1.2.0 review. It is **not** a new
IDtracker run, a reviewed identity correction, or a replacement PDF/video.
The source files and prior outputs were left untouched.

## Rule change

A group can continue through a short gap with membership but no position.
When a member has a raw label on a separate blob, that blob can propose a
split even if it is beyond the *pile's* 100-pixel one-frame movement gate.
The entire pile cannot jump to that blob. The partition must persist for three
consecutive frames, and each proposed branch must advance at most 100 pixels
between those frames. The disputed members have no canonical position while
the split is pending; their rows are flagged ambiguous. An unlabeled blob
can carry the other members only when it does not bear an unrelated ID label.
A one-frame conflicting ID does not end the pile.

This deliberately leaves a distant three-ID blob unresolved if accepting its
label would require an unsupported jump. It should be inspected in the video,
not counted as a confirmed pile or assigned to a distant beetle.

## Box 2 replay checks

| Check | Model 1.2.0 | Model 1.3.0 preview |
|---|---:|---:|
| Raw-labeled distinct-blob coordinates overwritten by a >60 px PSC position, animal-frames | 17,247 | 0 |
| Frames with a >=3-ID blob whose labeled identities are split, absent, or >60 px away | 343 | 47 |
| Canonical missing animal-frames | 2,789 | 3,339 |
| PSCP_BLOB animal-frames | 28,815 | 13,696 |
| Adjacent canonical steps >100 px | 1 | 0 |

The extra missing frames are intentional uncertainty rather than forced
locations. The large fall in PSC counts does **not** by itself establish
better biological accuracy; it shows that this model makes substantially
fewer unsupported colocation claims. The 47 remaining three-ID blob frames
and other ambiguous intervals need video review.

At 4022-4023 the proposed split of beetles 1 and 2 is unresolved; at 4024
they separate. Beetle 2 is no longer forced onto beetle 1 at frame 4125.
At 4187 the three-ID blob conflicts with stale group assignments and is
flagged; by frame 4200 beetles 2, 3, and 5 share its supported location.
At 6459-6460 beetle 1's separate raw detection makes its prior pile
ambiguous; by 6461 it is released. Thus the old 171-frame false PSC placement
after 6459 is removed. None of these raw identity labels is certified correct
without source-video review.

The source trajectory has 16,426 frames and six animals. The local replay
used `persistent_groups.py` 1.3.0 with social radius 60 px, maximum step 100
px/frame, three-frame split confirmation, gap growth 20 px/frame, gap cap 300
px, and maximum reacquisition gap 30 frames. `tests/test_persistent_groups.py`
contains synthetic regressions for the far return, one-frame false label,
moving pile across a detection gap, and distant three-ID conflict.

The active 2026 Firebird dyadic batch uses its previously staged code. Its
outputs must retain their recorded older model version. A new, separately
named postprocessing pass is needed to apply model 1.3.0 to those results.
