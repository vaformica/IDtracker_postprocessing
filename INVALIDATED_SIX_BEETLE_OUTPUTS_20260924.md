# 2024 six-beetle PSC output invalidation — 24 September 2026

The prior six-beetle postprocessing outputs were withdrawn at Vince's request.
They are **invalid for biological analysis** because persistent-group model
1.2.0 could keep an identity in a stale pile despite sustained separate raw
detections. In Box2_OLD, one raw ID was placed about 311 pixels away from its
own detected blob at frame 6459 and remained wrong for 171 raw-present frames.
The model also split a blob labeled with three identities during a 214-frame
interval. These are postprocessing failures; raw IDtracker tracking can also
lose or swap identities and is not certified by this finding.

The withdrawn Firebird batch was
`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/grouptrial_2024_selected_postprocess_20260923_2044utc`.
Its 11 analyses and videos used model 1.2.0 and must not be cited or reused.
Before deletion, the original selection plan SHA-256 was
`b21ec753f3e684ca6cedbcbb090f4fe7c10b7caefb302a52d44989759944fb06`.
The two withdrawn ZIP hashes were
`77826e204b8fbc931e116ea3d55e3f2df2bfe4ea0f6fe4bb246b7c55c1496896`
and `3fd64cf0a18727a91094427fdfe3d18f42ed2f9876b1bfd2e88bacd82465bd63`.
Hashes are recorded solely to identify and reject any detached old copies.

The original videos, student TOMLs, selected IDtracker sessions/trajectories,
and tracking-setting comparisons are distinct source material and remain
intact. A new analysis must show its persistent-group model version, code
hashes, source trajectory hash, and human-review status in its manifest.

Model 1.3.0 at commit `3d95261` changes split handling. It is a candidate
replacement, not a validated biological dataset. Two difficult trials must
pass frame-level and video review before the remaining 2024 analyses are
released. The 2026 dyadic outputs using the shared older engine also require
an impact audit and, if affected, a separately versioned rerun.

## Further invalidation: PSC 1.3.0

Vince's review of `groupagetrial04_062124_Box01_MIX` found that model 1.3.0
still allowed an unseen identity to leave a pile for a distant raw label. At
frame 994, beetle 1 was pulled about 890 pixels from its pile with beetle 2
to a blob near beetle 0. Similar false transfers occurred for beetle 0 near
frame 2710 and beetle 5 near frame 9172. The split-confirmation branch had
bypassed the 100-pixel-per-frame gate. The model-1.3.0/processor-0.8.1-group
11-review ZIP and all its derived movement/fungus/contact outputs are therefore
**WITHDRAWN**. The old ZIP and local extracted folder have been moved under
`outputs/WITHDRAWN_grouptrial_2024_psc_v130r081/`; the Firebird ZIP has a
`WITHDRAWN_` prefix and its root has a do-not-use marker. Source tracking,
TOMLs, and videos remain unchanged.

PSC model 1.4.0 at commit `0e61a75` is a validation candidate. It applies a
per-beetle speed gate to split branches and changes of pile, rejects brief
distant raw-ID bursts, and records a hidden member as `UNRESOLVED_SPLIT` when a
multiway split cannot be assigned to one branch. The model deliberately
reports more unknown-location frames rather than fabricate a supported path.
It must pass independent six-beetle and dyadic validation before any new batch
is released. The zero-conflict screen used for 1.3.0 was insufficient to catch
these errors and must not be cited as identity validation.

## Historical 1.3.0 replacement attempt — superseded

The two selected stress tests, `groupagetrial01_062024_Box01_OLD_TEst`
and `groupagetrial04_062124_Box02_OLD`, completed with PSC model 1.3.0.
Automated checks found no raw-label-versus-PSC distinct-blob overwrites and
no adjacent canonical step above 100 pixels in either trial. PDF rendering
and selected video frames were inspected. There are still 27 and 47 frames,
respectively, in which a blob labeled with at least three IDs conflicts with
the derived assignment. These remain explicitly **UNREVIEWED** and require
human judgment before biological interpretation.

The new Firebird batch is
`/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/grouptrial_2024_pscp_v1_3_0_20260924_0244utc`.
Slurm array `898765` was submitted for the other nine distinct eligible
TOMLs; its completion had not yet been verified when Firebird SSH became
unreachable. The new outputs must be packaged only after all 11 tasks have
the `COMPLETE_UNREVIEWED` state and a manifest declaring model 1.3.0.

An impact audit of ten high-PSC 2026 dyadic reviews found five with the same
class of conflict under model 1.2.0. The old dyadic finalizer array `898686`
was canceled. Its outputs must not be released as corrected results. Two
stress-test dyadic reruns using model 1.3.0 were submitted as array `898766`;
the remaining 97 trackable configurations await their validation. Original
dyadic TOMLs, IDtracker trajectories, and immutable receipts are retained.

## Further invalidation: shared PSC model 1.4.0

Vince found that in `groupagetrial01_062024_Box02_MIX`, beetle 0 visibly
leaves a pile with beetle 5 near frame 14012. IDtracker has no coordinate for
beetle 0 through frame 14561, but the exported blob evidence contains a
continuous unlabeled moving detection from frame 14021 to 14561. It joins a
smooth, singly labeled beetle-0 detection at frame 14562. Model 1.4.0
confirmed the late raw identity after ten frames but left the preceding
moving detection assigned to the old pile. This wrongly credited beetle 0
with pile movement and fungus occupancy. The preview and full 1.4.0
GroupTrial and dyadic outputs are **WITHDRAWN**. Arrays 899408 and 899414
were canceled. Their original tracking, TOMLs, and logs remain unchanged.

The next candidate, PSC model 1.5.0, adds a conservative backward trace from
a sustained raw reidentification through a unique unclaimed unlabeled blob
path back to the former pile. It marks that path as inferred and ambiguous,
and flags raw-versus-PSC identity conflicts explicitly. This is a hypothesis
for video review, not ground truth. Only new, fully validated 1.5.0 bundles
may replace the withdrawn outputs.
