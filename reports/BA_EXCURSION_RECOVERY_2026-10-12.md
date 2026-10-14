# BA excursion repair: targeted second review

AI-written by Codex, 12 October 2026. Development proposals; not applied to scientific outputs.

VAF accepted many targeted jump repairs but identified remaining errors in D4
(frames 2007–2011) and two BA_092 stretches. The preceding patch required every
changed position to be at least 50 pixels from the original, which excluded
D4's smaller initial deviation and prevented a complete repair. In BA_092, the
forward recovery had become stuck while the backward path followed the beetle;
requiring agreement over the whole run rejected otherwise useful local evidence.

The new separate experiment keeps every previous replacement exactly. It admits
a 20-pixel lead-in only within a supported excursion containing a displacement
of at least 50 pixels and an original step over 100 pixels, with both observed
flanks reconnecting through steps no larger than 30 pixels. It also tests short
(one to 15-frame) directional candidates against the images at both original
flanks. Every candidate patch must match both flank patches at normalized
correlation >=0.65. Competing eligible paths differing by more than eight pixels
veto the patch. Original missingness is preserved; insufficient support leaves
the original track and a review concern, not an invented path or silent deletion.

Directional candidates come from the frozen full-resolution recovery experiment.
The additional appearance check uses the existing full-resolution crop review
MP4s, which are compressed, not raw camera pixels. All new positions therefore
remain proposals; patch correlation is not a calibrated biological confidence.
No source video, TOML, tracking session, production processor or turtling rule
was modified, and no IDtracker jobs were run.

| Run | Large steps after previous patch | After new proposal | Additional changed positions |
|---|---:|---:|---:|
| D4 | 5 | 3 | 11 |
| BA_092 | 92 | 2 | 69 |
| BA_065 | 14 | 10 | 7 |
| BA_071 | 6 | 0 | 10 |
| BA_001, BA_004, BA_015 | 0 | 0 | 0 |

Counts refer to adjacent observed steps over 100 original pixels, not confirmed
errors or accuracy. Every prior replacement is identical and all missingness
masks are unchanged. No new large steps were introduced in the seven runs.
D4 2008–2011 now has replacements. Frame 2007 is unchanged: the extracted image
appears close to the beetle, but VAF's original 2007–2011 note remains intact and
the boundary is displayed for review. Do not reinterpret that note as approval.

The reviewer contains nine clips (855 frames, 28.5 seconds at 1x), prioritizing
the three rejected scenes, then additional repairs and a clean comparison.
Both video trails and frame-labeled trace plots are visible by default. Separate
trace-only decisions flag suspicious paths without approving beetle positions.
Video acceptance covers new replacements only (or displayed tracking in the
unchanged comparison). Export schema is `ba-excursion-review-v1`, filename
`BA_excursion_review_scores_20261012.json`. Blank or notes-only scenes are not
scored; neither trace plausibility nor a smooth path establishes correct tracking.

Evidence root: `outputs/ba_excursion_recovery_20261012/`. Per-run arrays, candidate
and applied-patch audits, summaries, cropped videos, plots and review data are
retained. Twelve static original/proposed image pairs and a trace plot were
inspected. Seven full-run regression checks, thirteen focused recovery tests,
27 first/middle/last clip alignment checks and actual viewer-script tests passed.
All nine encoded frame counts were verified. Browser playback was not tool-tested.
These are engineering checks, not independent biological validation. Review the
new proposals before considering wider application.
