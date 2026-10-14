# Focused BA boundary review: a substantial missed episode

Both VAF decisions are complete. The onset review changes the assessment of the detector: BA060 was already on its back at **frame 3942**, almost 99 seconds before the automatic flag begins. This is a substantial false-negative interval, not a small timing adjustment. The detector remains useful for proposing scenes, but automatic turtling durations should not be treated as reliable unattended measurements.

| Case | Latest human score | Frozen 0.4 result | Remaining disagreement |
| --- | --- | --- | --- |
| BA060 onset | 3942–6750 in the new scene; previous score continues through 7499 | Flags begin at 6910 | 3942–6909 missed: 2,968 frames, 98.93 seconds across combined reviewed coverage |
| FRESH_16 righting | On back through 6346 | Flags continue through 6375 | 6347–6375 extra: 29 frames, 0.97 seconds |

## What the new footage establishes

The first scene covers 822–6750, with no turtling scored before 3942. Its positive interval is 3942–6750, all 2,809 frames of which are missed by both frozen 0.3 and 0.4. Combining this with the earlier 6600–7499 annotation produces continuous human-confirmed on-back coverage at 3942–7499, without double-counting the 151 overlapping frames. The newly reviewed coverage adds 5,778 frames. Nothing here establishes posture after 7499 or outside the displayed windows.

All 2,968 missed positive frames in that combined interval have finite x/y coordinates and an open experimental recovery gate. The stored 0.3 evidence is `no_candidate_not_posture_label` throughout. Thus coordinate absence and recovery gating do not explain this failure: the trajectory detector supplies no supporting candidate until much later. Finite coordinates do not by themselves prove tracking accuracy. The 0.4 backward extension recovers only its permitted 300 frames, reaching 6910; that limit was already flagged as an uncertain onset.

The second scene covers 6200–6519. VAF now places the last on-back frame at 6346, versus the previous score's 6358. The new note reads: “Takea a few frames to flip over completely.” The 12 conflicting overlap frames, 6347–6358, are recorded explicitly. The latest focused annotation governs this displayed scope in the new comparison; both original exports remain unchanged. This is a boundary-label revision, not a detector regression. The frozen 0.4 result still improves over 0.3, which continues through 6397 and has 51 extra frames within this scene.

## Interpretation and next development step

The fresh-clip percentages reported before this focused review are historical results against those earlier labels. They must not be presented as evidence that long missed episodes are solved. This targeted follow-up is not independent or random validation, and combining its error percentage with unrelated earlier tests would be misleading. Flailing remains unassessed.

The next useful investigation is the actual posture and motion around 3942 and during the missed interval: compare the frozen feature evidence with nearby upright footage and known on-back examples. Simply extending the backward search by another 3,000 frames would fit this case without establishing a general rule and could create long false events in upright animals. A new detection strategy must be tested against both these missed frames and the circling/injury negatives before promotion.

Righting should have a documented annotation convention, acknowledging the transition over several frames. Preserve the exact 6346 label and its note; do not silently replace it with a tolerance band or the earlier 6358 endpoint. Human-review alerts remain appropriate for prolonged ambiguous posture and uncertain boundaries. No new detector fit, tracking job, exclusion, or production regeneration was performed during this import.

## Records and dashboard status

Local evidence: `outputs/ba_focused_boundary_results_20261012/`. Firebird: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_focused_boundary_results_20261012/`. The original export, `COMPARISON.json`, `INPUT_VERIFICATION.json`, and the evaluation script preserve the new score, displayed-only unions, revision audit, and frozen prediction hashes. Annotation/state consistency, clip identity, inclusive intervals and an independent interval-set confusion-count check passed.

The 121-run QC dashboard remains the preserved pre-import snapshot, including its prior human coverage and counts. This avoids invalidating manual-flag exports already tied to that index hash. Its BA060 onset-search-limit flag is still relevant, but this report is the current behavioral interpretation. A separate review-update record marks the substantial known miss and latest righting boundary; no old dashboard, sidecar, or score file is overwritten.
