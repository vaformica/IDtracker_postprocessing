# Pile continuity and human review layer — 23 September 2026

The shared post-processor now distinguishes three pair states that previously
blurred together: independently assigned beetles in proximity, a detected
blob carrying an inferred group member (PSCP), and persistent pile membership
with **no detected location**. The last state is gray in the HTML timeline and
has `unresolved_contact_partners` in `frame_data.csv`. It adds no coordinates,
movement, or automatic fungus occupancy.

Version 1.1.0 introduced bounded gap reconnection, retained in 1.2.0. After a detection gap, membership
persists. A returning blob can reconnect the group within a bounded radius
that grows with elapsed frames. Defaults: 20 px/frame growth from the 60-px
social radius, a 300-px cap, a 30-frame maximum automatic gap, and three
consistent separate detections to split a group. These are tunable in the
Firebird post-processing GUI and recorded with each automatic result. Longer
or ambiguous gaps remain unresolved for human review. These parameters are
engineering hypotheses, not measured beetle-speed limits.

### One detected blob, several IDtracker coordinates (model 1.2.0)

Vince identified a missed 1–5 PSC episode in the 2024 OLD sample. The
segmentation evidence has one blob near them while IDtracker supplies finite
coordinates for both IDs. Model 1.1.0 counted both as assigned and excluded
most of their shared-blob episode from PSC. Model 1.2.0 gives one blob at most
one visible identity: the coordinate closest to its centroid is the anchor,
and the other group member is an inferred PSCP position. In frames 2200–2600,
pair 1–5 now has 389 position-supported PSC frames instead of 39. At frame
2300, beetle 5 anchors the blob and beetle 1 is inferred there. Which ID is
actually visible remains a review question; blob evidence alone cannot prove
that a fight occurred or that a hidden beetle never separated.

The HTML now supports dragging across a pair's timeline row to select an
inclusive range, then applying PSC, no PSC, or locationless pile with one
button. The older detailed controls remain for location, proximity, and
fungus edits. A selected range highlights on the timeline.

The portable HTML is now an attributed review interface for any supported
animal count and fungus count. A reviewer selects a beetle, partner, inclusive
frame range, decision, and reason. Available corrections cover PSCP, visible
proximity, location (raw assignment, missing, or a partner's detected position),
and fungus identity. The timeline, overlay, and status cards update without
changing the source tracking. Export/import uses a dated JSON decision log
bound to the exact automatic manifest and canonical-state SHA-256 hashes.
`apply_review_decisions.py` replays that log atomically into a new reviewed
frame CSV, beetle/pair summaries, state archive, audit log, hash manifest,
and optionally another portable HTML/video folder. `raw_x` and `raw_y` always
retain the original IDtracker coordinates. Each corrected row carries a
`human_intervention` flag. Real human decisions are still needed before these
logs become a training set.

Global pile and ROI algorithm changes require a new automatic processing run;
frame-specific review corrections do not silently change those model settings.
The HTML displays the settings used for its run. All automatic and reviewed
outputs remain scientifically unverified until the source video is examined.

## Validation

- 111 tests pass, including gap reconnection, locationless contact export,
  portable viewer construction, human-decision replay, raw-coordinate
  preservation, and refusal to overwrite an output.
- A new analysis of the 2024 six-beetle OLD frames 2200–2600 produced a PDF,
  frame CSV, and synchronized review clip. At frames 2317–2318, beetles 0 and 2
  have unresolved group membership with missing locations. The browser review
  displayed that state without assigning a fungus or drawing a path through
  the gap. The 401-frame MP4 and timeline sought to the same global frame.
- A two-beetle 2026 fight window, frames 820–1120, was reprocessed from the
  raw coordinate array preserved in the earlier hashed canonical bundle and
  the previously exported Firebird detections. Its new HTML/video review
  showed PSCP at frame 850 with aligned playback. This local validation input
  is derived; it is not a fresh copy of the original Firebird trajectory file.
- Replaying an empty review log reproduced the original frame rows for both
  the two- and six-beetle new-model bundles, and made portable reviewed HTML
  folders. A separate two-beetle test applied actual correction decisions and
  verified the reviewed coordinates, pair counts, fungus tally, and source
  raw coordinates.

## Review examples

- [Revised six-beetle 1–5 HTML](../results/review_editor_validation_20260923/six_gap_one_blob_v12_final_review/interaction_review.html), [PDF](../results/review_editor_validation_20260923/six_gap_one_blob_v12_final_analysis/six_gap_one_blob_v12_final.pdf), [frame CSV](../results/review_editor_validation_20260923/six_gap_one_blob_v12_final_analysis/frame_data.csv).
- [Revised dyadic HTML](../results/review_editor_validation_20260923/dyad_one_blob_v12_final_review/interaction_review.html), [PDF](../results/review_editor_validation_20260923/dyad_one_blob_v12_final_analysis/dyad_one_blob_v12_final.pdf).

Each HTML requires its adjacent `review_video.mp4`. For reliable browser
seeking, use `python serve_review.py REVIEW_FOLDER --port 8769` and open the
localhost URL printed by the script. The older generic `python -m http.server`
did not serve MP4 byte ranges in our browser test, so its apparent slider
position could move while the video stayed at time zero.
