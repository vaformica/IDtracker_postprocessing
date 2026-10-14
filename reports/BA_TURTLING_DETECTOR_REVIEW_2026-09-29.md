# BA turtling: detector review and validation proposal

The recovered July 24 user description defines the target as a beetle flipping over and flailing in circles. The requested outputs were candidate frames and candidate frames divided by detected frames. This behavior is not equivalent to ordinary immobility. Whether quiet pauses while overturned belong in total duration is awaiting clarification.

## Current implementation, verified September 29

`processor.compute_turtling_candidates` uses 120-frame sliding windows. It requires at least 95% observed coordinates, no observed adjacent step above 20 px, at least 120 px of path from steps at least 1 px, a 90th-percentile radius between 5 and 35 px, cumulative absolute heading change of at least three rotations, and net displacement/path length at most 0.25. Every observed frame in a passing window is marked; overlapping windows are unioned.

Important limitations from code inspection:

- Absolute heading change counts back-and-forth turns. It is not a measurement of completed circles or body orientation.
- A single large step vetoes an entire candidate window.
- A small-radius or nearly stationary overturned animal may not pass the path/radius thresholds.
- Labeling whole overlapping windows can extend candidate boundaries beyond the active behavior.
- Pixel thresholds are not normalized to beetle size or video scale.

A diagnostic synthetic counterexample was run locally: 120 frames moving back and forth along one straight line over a 20-pixel span produced 120 candidate frames. There were no circles. This demonstrates a feature ambiguity, not the false-positive rate in real BA data.

## Proposed development sequence

1. Preserve the present detector as an explicitly versioned baseline. Do not silently replace pilot statistics.
2. Review video examples: clear overturned/flailing bouts, normal tight turns, grooming, wall-following, stationary jitter, missing detections, and uncertain posture. Include randomly sampled non-candidate intervals to look for missed events.
3. Keep separate labels for inverted posture and active flailing, with an unknown state when video does not support a decision. Record onset/end and reviewer identity.
4. Evaluate candidate features across several window lengths: local spatial extent, accepted path, net progress, reversals, circular winding about a local center, angular-direction consistency, and tracking completeness. Do not require one rotation direction if genuine flailing reverses. Use body-size normalization only where a reliable size estimate exists.
5. Inspect the raw video crop for posture/body/leg motion. Centroid-only detection can prioritize review but cannot establish flipped posture. If manual confirmation is the bottleneck, test a labeled video/pose classifier after assembling representative training examples.
6. Choose thresholds on training videos; evaluate on held-out whole source videos, not interleaved frames from the same recording. Report event recall, false alarms per assessed video duration, frame precision/recall, onset/end errors, and total-duration bias separately.
7. Use stable bout boundaries (different onset/offset persistence criteria) only after validation. Keep missing/occluded frames unknown rather than turning them into confirmed turtling.

This is a proposal, not a validated new detector. SimBA provides a published example of supervised, interpretable behavioral classification; its results do not establish performance for overturned beetles: https://www.nature.com/articles/s41593-024-01649-9 .
