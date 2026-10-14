# Two different causes of long missed BA episodes

AI-written investigation by Codex, 13 October 2026. Development experiments only; frozen 0.4 and production remain unchanged. Evidence and executable scripts: `outputs/ba_quiet_qc_experiment_20261013/`.

BA030 has no baseline candidate and no 0.3 anchor. Of 6,514 four-second windows wholly inside its missed positive interval, 6,513 fail the 120-pixel qualifying-path requirement and 6,252 fail the 5–35-pixel radius requirement. Median qualifying path is 56.76 pixels and radius is 1.70 pixels. Turning is comparatively strong: median 6.93 rotations under the detector's centroid-derived measure. These numbers characterize tracking motion, not anatomical rotation or flailing.

BA060's 2,849 fully missed positive windows all fail path length; 2,731 fail turning and 2,290 fail straightness. Median qualifying path is 17.86 pixels and turning 0.79 rotations. All windows in both audits pass finite-coordinate and maximum-step checks. This confirms the miss is not explained by missing tracking or jumps. BA030 needs an initial candidate; quiet-tail and capped backward-extension rules cannot create one. BA060 has a later anchor but lacks earlier support. Extending backward to the known human flip would conceal this distinction.

## What the experiments recover, and what they falsely flag

All additions are compared with the unchanged frozen 0.4 mask, using full human-scored frames in the six-run set. BA060 uses scored coverage through 7499; later frames are not treated as negative. Five controls are VAF-negative complete runs.

| Experimental addition | BA030 missed frames recovered | BA060 missed frames recovered | New positive flags on five negative controls |
|---|---:|---:|---:|
| Remove qualifying path minimum | 665 | 258 | 146 frames |
| Remove path minimum and lower radius bound | 6,572 | 258 | 513 frames |
| Remove path and turning minimum | 665 | 1,778 | 1,756 frames |
| Quiet 10-second windows within 15 pixels | 6,630 | 2,938 | 16,260 frames |
| Remove path/lower-radius minimum, require a 20-second continuous candidate | 6,000 | 0 | 0 frames |

The last rule was tried after inspecting the errors, so its 20-second persistence is explicitly post hoc. It recovers 200 of BA030's 221.1 missed seconds, leaving 633 frames missed. It creates no new flags in the five complete negative controls or the scored portions of seven earlier upright/circling examples (BA015,025,039,041,049,077,080). Those earlier examples are development data, not independent validation. This is promising as an additional review trigger, not evidence of a generally reliable posture classifier. It does not solve BA060. No candidate was promoted or added to the official masks.

The quiet-window grid used 5/10/20 seconds and radii 10/15/25 pixels with finite, recovery-eligible coordinates and a 20-pixel adjacent-step guard. Every setting adds flags to at least four of the five negative controls. Quietness alone is therefore inadequate for a turtling label. Even as QC it has substantial review burden: the 10-second/15-pixel option flags 542 seconds in negative controls.

## Useful QC without pretending to know posture

Separate `QC_SIDECARS.json` records retrospective quiet-post-recovery intervals, original 0.4 candidates, and tracking-unknown intervals for all seven cases. Quiet warning intervals do not establish a flip or its onset. Missing observations are never filled, and qualifying quiet windows never span gaps. These sidecars are local experiment output, not wired into the active scorer or production QC.

A useful next review interface should distinguish: (1) localized irregular-motion candidate; (2) prolonged quiet posture requiring visual inspection; (3) tracking loss, where posture is unknown; and (4) camera/light disturbance. A tracking loss may coincide with a flip, but is not evidence that one occurred. Put context before and after each event in the review clip; keep a continuous source-video view available even when coordinates disappear. Do not convert warning duration into turtling duration.

My next development recommendation is to freeze the sustained irregular-motion candidate as a separate BA QC experiment and test it against additional untouched recordings before changing labels. In parallel, evaluate a short image sequence around transitions using an arena view or last reliable location when tracking is absent, with explicit abstention when the animal cannot be located. A temporal posture model should be scored on on-back, upright-still, circling, righting, shadows and tracking failures. The prior image model's failures remain unresolved; no claim is made that adding images alone fixes the problem.

No dyadic extension, new tracking, source edits, or production release was performed. This investigation evaluates coordinates and existing attributed labels; it does not provide a fresh visual review or validate flailing.
