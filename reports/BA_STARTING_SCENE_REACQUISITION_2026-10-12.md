# BA starting scenes: recover visible beetles, retain uncertainty during coverage

AI-written by Codex, 12 October 2026. Targeted development proposals, not a scientific release.

The latest reviews rejected D4 and BA_092 at frames 1095–1139 and BA_065 at
1373–1470, while accepting BA_071's starting scene. Inspection shows that the
rejected scenes still contained original errors which earlier proposals had
left unchanged. D4 and BA_092 started before a usable tracking reference. BA_065
also shows a hand or sleeve over the arena; some errors coincide with actual
coverage of the beetle's area, not merely a shadow. This visual observation does
not establish a general disturbance detector or explain every tracking error.

The separate `ba_stationary_reacquisition.py` experiment uses a dominant cluster
of stable positions in each selected short scene as an appearance reference.
It requires at least ten reference frames, at least 70% of stable observations
in the same 15-pixel cluster, and matches templates from two separated reference
frames. Each candidate must agree between templates within five pixels, achieve
normalized correlation >=0.8, and beat alternatives by >=0.03. Changes smaller
than 20 pixels are retained, and a scene must contain a supported displacement
of at least 50 pixels. These provisional thresholds are tested only in the
selected nearly stationary scenes, not applied automatically across whole videos.

Where a short, internally bounded image-failure interval also has a large
reference displacement, the experiment proposes missing observations instead
of a guessed position. In BA_065 these are 1442–1443 and 1447–1448. Static images
show partial/full coverage around these frames. VAF must review both the
replacement positions and missing-value proposals; original coordinates remain
available in every output. Insufficient matching alone is not a universal rule
for deleting original observations.

| Scene | New replacement positions | Newly proposed missing observations |
|---|---:|---:|
| D4 1095–1139 | 4 | 0 |
| BA_092 1095–1139 | 3 | 0 |
| BA_065 1373–1470 | 14 | 4 |
| BA_071 accepted starting comparison | 0 | 0 |

The new D4 positions cover 1095–1098; BA_092 covers 1095–1097. BA_065 replacements
cover 1378, 1387, 1390–1398 and 1444–1446. The latter three frames show the beetle
again despite the hand elsewhere in the arena. All accepted scenes in these
four run arrays are exactly preserved; other run arrays are untouched. No
production code, source tracking, source TOMLs or behavioral outputs changed.
The absence of >100-pixel steps in these clips is not proof of correct recovery,
especially because four transitions now involve missing observations.

Four clips total 233 frames (7.77 seconds at normal speed). Original, prior-patch
and new positions are available in the viewer, with trace plots visible by
default. The viewer labels proposed missing frames explicitly. Video acceptance
covers new replacements AND proposed missing observations; trace judgments remain
separate. New export schema: `ba-starting-review-v1`; expected filename:
`BA_starting_review_scores_20261012.json`.

Evidence root: `outputs/ba_starting_recovery_20261012/`. Full run arrays preserve
raw and previous coordinates; audits retain reference frames, match scores and
candidate decisions. Five focused tests, accepted-scene preservation checks,
12 first/middle/last alignment checks and viewer-script tests passed. Four encoded
clip counts were verified. Ten static comparison pairs were visually inspected.
Browser playback was not tool-tested. The masking and stationary assumptions
need human review before any broader adoption.
