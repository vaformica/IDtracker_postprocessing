# Unified 100-pixel jump cleanup — 28 October 2026

## Decision

Vince selected one shared cutoff for BA and aggression/fight post-processing:
**a movement step strictly greater than 100 original-image pixels between
adjacent frames is treated as an impossible one-frame jump. A step of exactly
100 pixels is retained.** This is a practical cleanup threshold, not a claim
about a beetle's validated biological maximum speed.

The same implementation is wired into the six-beetle processor for consistency,
but six-beetle work remains on hold. This policy change does not authorize or
start any scientific runs.

## What the cleanup does

1. Preserve the source tracking arrays and pre-cleanup coordinates.
2. Detect adjacent-frame steps over 100 pixels in the analysis layer.
3. For a paired, short out-and-back excursion, interpolate affected positions
   only when the gap is no more than 15 frames and the bounding coordinates are
   no more than 100 pixels apart.
4. If those conditions are not met, leave affected analysis positions unknown
   rather than invent a path.
5. Label corrected/interpolated/removed positions and retain event details in
   the audit outputs. Use cleaned positions for downstream location and movement
   calculations; keep original data available for review.

The turtling detector's own allowed step size and the social group's gap
reconstruction speed are distinct controls. Their numeric values must not be
confused with this general one-frame jump cleanup cutoff.

## Code and records

The shared implementation is `jump_policy.py` version
`1.1.0-unified-100px`. The standalone processor is
`0.8.3-unified-100px-jump`, the BA entry point is
`0.4.0-unified-100px-jump`, and the shared dyadic/six-beetle processor is
`0.8.4-unified-100px-jump`. The policy now applies across all animal counts in
those analytical paths. `METHODS.html`, `DATA_DICTIONARY.md`, the README, the
six-beetle handoff, and the changelog record the same rule.

## Validation and scope

The prior source-checkpoint test log is retained unchanged. It records 271
tests attempted: 251 passed, 2 failed, and 18 errored. The two failures concern
expectations that conflict with applying location cleanup; the errors include
missing optional modules and source-package fixture files. That historical run
does not validate this updated policy. **No tests were run for this change**,
and no scientific tracking or post-processing run was started. Existing
scientific outputs remain pinned to their original code and settings until
separately reviewed and regenerated under explicit authorization.

## Human-facing explanation

At 30 frames per second, a 100-pixel change from one frame to the next is used
as the practical boundary for an impossible jump. If a path briefly jumps away
and returns to a nearby location, the processor may fill that short interruption
with a straight-line estimate. If it cannot establish a safe short repair, it
marks those positions unknown. In both cases the original trace stays in the
record so a reviewer can see what the software changed.
