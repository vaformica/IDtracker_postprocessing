# Shared video and tracking QC

Development version 0.1.0 adds the same review-only checks to BA, dyadic, and
six-beetle pipelines. It does not change trajectories, PSC, behavior rules,
tracking intervals, or human approval. Existing releases are not regenerated.

## What belongs together, and what stays separate

| Layer | Current evidence | Scope and interpretation |
|---|---|---|
| Recording | Every-frame low-resolution brightness changes; phase-correlation translation | Source recording; possible disturbance, not proof of a light switch or camera bump |
| Tracking | Missing observations/bouts, >100-pixel adjacent steps, outside arena, exact stationarity, synchronous jumps across IDs | Per animal and run; missing IDs can be ordinary social occlusion |
| Behavior and reconstruction | Links to existing BA candidate/QC reports; unchanged PSC outputs | Turtling, inferred contact, and identity correctness still require their own review |
| Human decisions | Existing attributed exclusion/review records remain authoritative | Never infer an exclusion or approval from an automatic flag |
| Collection completeness | Existing census and configuration reconciliation | A configuration is not automatically a unique animal; no new registry is introduced |

This is the first shared checker, not a validated universal classifier. It cannot
reliably identify people, determine posture, detect every small camera motion,
or prove ID correctness. Per-recording calibration and held-out visual review
are still needed. Large changes after a light switch may persist even if the
instantaneous switch frames are excluded. A single confidence percentage would
hide these distinctions, so none is produced.

## New pipeline runs

`run_ba_pipeline.py` writes `unified_qc.json` and `unified_qc.html` into its new
bundle. Its video viewer links to QC. `run_group_pipeline.py` and
`run_six_beetle_pipeline.py` write the same files in the analysis folder and
reference their hashes in the pipeline receipt; the output guide identifies them.
The shared Firebird GUI deployment includes the new module. Historical frozen
batch scripts/code snapshots retain their old behavior until explicitly redeployed.
The standalone legacy processor/GUI is not silently upgraded by this change.

Source screening defaults on and decodes every frame at 160×90, preserving the
original frame index. No temporal subsampling is used: this matters for a two-frame
flash. It adds decoding time. Use `--qc-cache-dir /path/to/shared/cache` across
cells from one recording; default pipeline caches are placed outside run bundles.
Caches are keyed by full video SHA-256, QC version, resolution, and thresholds.
Concurrent first users may duplicate computation, but write cache files atomically.

`--skip-qc-video` explicitly records NOT_ASSESSED. Decode failures record FAILED
and their reason; they never become a clean result. Raw trajectory QC still runs.
Incomplete coverage is an error. No flags is not approval. All automatic output
remains UNREVIEWED. The reported completion flag covers implemented checks only,
not biological validity or the unassessed dimensions.

The common report has missingness per animal, disconnected raw XY traces,
a recording-brightness trace, and expandable frame-level evidence by reason.
Existing synchronized review footage is linked rather than duplicated. Source
frame-pair transitions are evidence ranges, not exact frames to delete. New checks
must retain machine-readable evidence and human-readable explanations.

## Standalone inspection of existing tracking

Run `python unified_qc.py --help`. Supply an original-frame trajectory, source
video, inclusive start/end, measured fps, and a new output directory. This writes
sidecars without editing existing analysis. The standalone CLI does not infer
an arena; outside-arena checks are unavailable unless supplied through the API.

The pure summarizer accepts explicit inclusive excluded ranges and computes
missingness on remaining observations, breaking steps and stationary chains at
gaps. It does not authorize them. Current production BA science still rejects
split tracking intervals. Do not use this QC addition to bypass that safeguard:
full gap-aware movement, behavior, PDF, and video processing remains separate work.

## Next development checks

1. Review actual lighting candidates against VAF's 1608–1609 annotation, including
   nearby frames that the automatic checker does not flag. Preserve disagreement.
2. Validate camera-motion hypotheses in separate recordings and normal-motion
   controls across BA, fights, and six-beetle videos. Synthetic translation proves
   implementation behavior, not biological specificity.
3. Combine sibling-cell evidence by source hash for collection-wide review; add
   configuration/session alignment and existing PSC/behavior uncertainty adapters.
4. Evaluate gap-aware analysis of the authorized 20-cell rerun, keeping intentional
   exclusions distinct from unexpected tracking loss and previous output versions.
