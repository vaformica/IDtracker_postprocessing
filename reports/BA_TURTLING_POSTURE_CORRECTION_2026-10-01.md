# Attributed posture correction, October 1

Vince accepted the first longer excerpt's timing and reported that the second
excerpt's flailing pause occurred while the beetle remained on its back.
The direct feedback is preserved in the new reviewed output's USER_FEEDBACK.json.

- First example: retain onset frame 6894 and the displayed interval through 7463
  (19 seconds). This later longer-context judgment supersedes the initial negative
  clip 7 label on frames 6894–6923; the original scored JSON stays unchanged.
- Second example: confirm overturned posture and inactive flailing at frames
  6072–6081. The separate review-assisted episode becomes 5645–6464 inclusive,
  820 frames / 30 fps = 27.333333 seconds. Original movement candidates remain
  810 frames = 27 seconds. Outside explicit posture labels, automatic candidates
  remain unconfirmed. The excerpt endpoint is not necessarily the biological offset.

Video timing resolution is 1/30 second, about 33.3 milliseconds; feedback accepting
precise timing does not establish millisecond measurement accuracy.

Module v0.2.0 applies attributed posture ranges to a separate episode mask, retains
raw movement flags, and exports evidence per frame. No general short-gap bridging
was introduced from one example. Human-confirmed posture can be recorded even
when coordinates are missing; missing tracking remains explicit in the baseline.
Quiet overturned time is counted as turtling, and active flailing remains separate.

New local artifacts: outputs/ba_turtling_reviewed_20261001/. New Firebird root:
/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_turtling_reviewed_v0_2_20261001.
Older development/scoring artifacts are retained. Both reviewed PDFs were rendered
and inspected; 13 targeted BA tests passed. The viewer at global frame 6072 shows
CONFIRMED OVERTURNED, flailing paused, and continued episode time.

Also repaired a development-only pipeline defect: the PDF filename must be assigned
before invoking the PDF renderer. No historical released outputs used this path.
