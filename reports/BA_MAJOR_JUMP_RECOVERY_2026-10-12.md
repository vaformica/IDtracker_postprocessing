# BA major-jump repair: preserve the usable track

AI-written by Codex, 12 October 2026. Development proposals, not approved corrections.

Vince's reviews showed that the earlier recovery algorithm often lost a visible
beetle even when IDtracker's original position was usable. D4 did contain useful
repairs. The objective is therefore to recover major shadow/light-related errors
without discarding otherwise usable runs or changing minor centroid differences.

The separate `ba_major_jump_recovery.py` development gate starts with an exact copy
of the original coordinates. A replacement must differ by at least 50 original
pixels, lie in a candidate segment touching an original step over 100 pixels,
and join observed original positions on both sides with no step exceeding 30
pixels. Candidate positions must already have passed the frozen full-resolution,
bidirectional image/detection recovery checks. Entire failing patches are rejected.
A large jump alone does not prove an original position is wrong. These thresholds
are provisional, not learned probabilities or validated biological cutoffs.

Missing input positions remain missing; weak recovery does not remove existing
positions. Unrepaired jumps remain in the raw-preserving proposal and are flagged
for review. This is not a claim that those retained positions are valid for every
analysis. No input trajectories, source videos, TOMLs, production processors,
turtling rules, or scientific outputs were overwritten.

The D4 export was preserved byte for byte and its hash, source video and scene
bounds checked. Its 14 accept, five visibility-only and one reject decisions have
different scopes. The revised D4 track preserves the rejected 3785–3791 scene.
All retained D4 replacements fall in previously accepted scenes; this does not
validate the rules on new cells or turn scene labels into frame-level truth.

Review order: D4, BA_092 (another cell of the D4 recording), the newly selected
BA_071 cell of that recording, then BA_065 from a different recording. BA_015,
BA_004 and BA_001 provide additional regression checks. The new viewer shows
60-frame trajectory trails and full-run plots by default. Only review decisions
for displayed scenes are exported, with a new schema and result hash.

The authoritative current counts and completion status are in
`outputs/ba_major_jump_recovery_20261012/SUMMARY.json`; the human-facing index is
`START_HERE.html` in that folder. Each review folder includes original/proposed
arrays, a patch audit, data hash, media hash and source receipt. Original candidates
remain frozen in their prior evidence roots. The extra BA_071 candidate generation
is recorded separately in the new root, with its selected configuration and job log.

Seven focused algorithm tests cover repair, wrong reconnection, missing and
available-position preservation, minor offsets and unsupported candidates. Viewer
checks exercise real page scripts for repeated frame stepping, presented-frame
synchronization, scoped decisions and hash-guarded imports. Media hashes and prior
encoded counts are checked before reuse. These checks are software evidence;
browser playback and biological accuracy are not implied by them.

## Completed comparison

| Run | Original >100 px steps | Proposed >100 px steps | Positions replaced | Original and proposed missing frames |
|---|---:|---:|---:|---:|
| D4 | 34 | 5 | 42 | 141 |
| BA_092 | 120 | 92 | 19 | 0 |
| BA_065 | 16 | 14 | 2 | 2 |
| BA_015 | 4 | 0 | 2 | 136 |
| BA_004 | 0 | 0 | 0 | 2517 |
| BA_001 | 0 | 0 | 0 | 0 |
| BA_071, new C4 cell | 14 | 6 | 5 | 0 |

The new C4 cell is from `Camera_1_40169154_20260627_1614_ACT2.mp4`, original
frames 1095–8294, source TOML ending `_C4.toml`. Firebird job 918398 completed
candidate generation and verified 7,200 encoded frames. Its raw array equals the
previously frozen BA_071 baseline exactly. The four review scenes cover flags at
1095–1109, 1754–1756, 1803–1808 and 2132–2136, with surrounding footage.
Only the last two contain accepted proposals under the new algorithm; the first
two remain review concerns. The exported decisions will determine whether these
proposals are visually correct.

Across all seven runs, no originally available coordinates become missing, and
no original missing observations are filled. Five representative static overlay
pairs and the D4 full-run trace were inspected. Seven algorithm tests and seven
viewer-script test runs pass. This is not a browser playback or biological
validation claim. In particular BA_092 retains 92 major jumps, so the method is
useful only as a partial repair proposal at this stage.
