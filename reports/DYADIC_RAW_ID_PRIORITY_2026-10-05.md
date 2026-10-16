# Hannah’s dyadic review: raw ID priority correction — 5 October 2026

## Outcome and status

Development **PSC model 1.6.0**, shared group processor **0.8.2-group**.
Both dyadic and six-beetle entry points use the corrected engine.
The existing 25-run PSC 1.5.2 dyadic review videos and 26-run PSC 1.5.1
six-beetle release have **not** been regenerated. The new replay is regression
evidence, **COMPLETED_UNREVIEWED**, not a biologically validated release.

Vince’s instruction after Hannah’s review: retain every available IDtracker ID;
call two tracked beetles within the centroid threshold proximity; use PSC only
for missing IDs; restore tracked IDs immediately after separation.

## Root causes and changes

1. The former one-blob-one-anchor rule replaced multiple available input IDs
   with one assigned anchor and inferred PSC members, often moving their
   coordinates to the blob centroid. A shared segmentation blob no longer
   invalidates available IDtracker coordinates.
2. Movement, split-confirmation and distant-return gates could suppress or move
   a returning ID. Available IDs now detach immediately from inferred groups
   and keep their exact input coordinates. Legacy confirmation arguments remain
   accepted but are explicitly inactive. The old delayed/backtraced identity
   reassignment path is no longer applied.
3. These rules lived in `persistent_groups.py`, shared by both group sizes.
   There was no independent, more refined six-beetle implementation to preserve.
4. Individual display and disappearance flags now distinguish an assigned
   partner from a missing ID. The pair may still have presumed contact when
   one member is inferred; the assigned individual is never labeled inferred.
5. Release validation now checks the raw-assignment invariant. It reports large
   retained raw jumps without rejecting their coordinates, but still rejects
   impossible inferred movement. Separate distance-summary cutoffs remain.

## Current rules

- Complete finite input x/y means **ASSIGNED**, at exactly that x/y, regardless
  of segmentation, displacement, duration of absence, or other available IDs.
- Two assigned centroids at distance **<=60 original-image pixels** qualify as
  proximity. This is not a body-length calculation or proof of physical contact.
- Only missing IDs can receive `PSCP_BLOB`. Starting contact requires proximity
  in the immediately preceding supported frame and a compatible current blob.
  Stale proximity or the larger movement radius cannot establish contact.
- Missing singleton detection continuity remains `BLOB_CONTINUITY`, not PSC.
  Missing-ID inference retains the 100-pixel one-frame bound, 300-pixel cap,
  20-pixel gap growth and 30-frame reacquisition limit. Competing unsupported
  attributions stay missing. Existing missing-group membership can outlive a
  detection gap without filling unseen coordinates.
- No upstream identity swap is silently corrected. “Raw” means the selected
  IDtracker trajectory array, which may already contain gap-processed positions.

## Hannah’s 14 examples

The original comments and colour assignments are preserved verbatim in
[the review fixture](fixtures/hannah_dyadic_review_2026-10-05.csv).
Reported frames are interpreted as **global source frames**, matching the review
viewer’s global counter. This is an explicit assumption; local playback offsets
are recorded separately for checking. No claim of new visual adjudication is made.

Short labels below:
- **A1/C1:** Camera_1_40169154_20260630_1342_FIGHT_ACT1.
- **Wrong A2:** Camera_1_40169154_20260630_1633_FIGHT_ACT2_PAPER_DATA_WRONG.
- **B2:** Camera_2_40359705_20260702_1536_FIGHT_ACT2.

| Video/cell | Global frame | Raw centroid distance (px) | Old ID 0 / ID 1 states | New result |
|---|---:|---:|---|---|
| A1 | 6707 | 56.33 | ASSIGNED / ASSIGNED | Both assigned; proximity, no PSC |
| C1 | 5995 | 45.28 | PSCP_BLOB / ASSIGNED | Both assigned; proximity, no PSC |
| C1 | 6571 | one ID missing | PSCP_BLOB / ASSIGNED | ID 0 PSC; ID 1 assigned; missing-ID inference still needs review |
| C1 | 6909 | 48.31 | ASSIGNED / PSCP_BLOB | Both assigned; proximity, no PSC |
| C1 | 7026 | 100.89 | MISSING / MISSING | Both assigned; outside 60 px; no proximity or PSC |
| C1 | 6780 | 63.72 | MISSING / MISSING | Both assigned; outside 60 px; no proximity or PSC |
| C1 | 6865 | 60.21 | MISSING / MISSING | Both assigned; outside 60 px; no proximity or PSC |
| Wrong A2 | 3071 | 57.64 | ASSIGNED / ASSIGNED | Both assigned; proximity; identity-swap report unresolved |
| Wrong A2 | 3605 | 42.22 | ASSIGNED / PSCP_BLOB | Both assigned; proximity, no PSC |
| B2 | 865 | 52.55 | ASSIGNED / PSCP_BLOB | Both assigned; proximity, no PSC |
| B2 | 1168 | 53.97 | ASSIGNED / PSCP_BLOB | Both assigned; proximity, no PSC |
| B2 | 1169 | 57.92 | MISSING / MISSING | Both assigned; proximity, no PSC |
| B2 | 1291 | 61.89 | MISSING / MISSING | Both assigned; outside 60 px; no proximity or PSC |
| B2 | 3243 | 79.43 | MISSING / MISSING | Both assigned; outside 60 px; no proximity or PSC |

The five examples previously assigned PSC despite both IDs being available now
retain both IDs and show proximity. All six examples where the processor lost
available IDs now retain them. C1 frames **6780 (63.72 px)** and **6865 (60.21 px)**
still do not meet the retained proximity threshold. A1 frame 6707 is **56.33 px**
and therefore qualifies under that rule regardless of apparent body length.
C1 frame **6571** still has a truly missing raw ID and remains a PSC hypothesis.
The colour/identity swap at Wrong A2 frame **3071** requires separate review;
both old and new outputs retain the same upstream labels at that frame.

## Recorded-input replay

All inputs were replayed from frame zero through the original analysis end,
then sliced to the original inclusive window, preserving initialization history.
Each selected raw array was compared exactly (including missingness) to the
frozen release array. Detection exports were checked against the original
manifest hashes. Original data and old outputs were read only.

| Dataset | Runs | Frames/run | Available raw animal-frames | Previously altered/suppressed assignments | Altered assignments in 1.6.0 |
|---|---:|---:|---:|---:|---:|
| Dyadic pilot | 25 | 7,200 | 333,708 | 38,259 | 0 |
| Six-beetle release | 26 | 9,000 | 1,228,727 | 150,922 | 0 |

“Altered/suppressed” includes a changed centroid, lost position, or a non-assigned
label while raw coordinates were available. These are animal-frame counts,
not counts of fights, identity swaps, or independently confirmed biological errors.
No new PSC pair contained two available raw IDs. Inferred movement bounds passed.
All **51 downloaded result hashes** matched the replay receipt.

## Evidence and reproduction

**157 tests passed** using `venv-mac/bin/python -m unittest discover -s tests -v`.
The complete test log and current code hashes are retained in the local audit
folder. These are software checks, not biological approval.

- Reproducible shared-engine replay: `audit_psc_raw_priority.py`.
- Local receipt and 51 output arrays:
  `outputs/psc_raw_priority_audit_20261005/replay/AUDIT_RECEIPT.json`.
- Four-video, 14-frame comparisons:
  `outputs/psc_raw_priority_audit_20261005/HANNAH_FRAME_AUDIT.csv` and `.json`.
- Remote isolated snapshot/results:
  `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/psc_raw_priority_audit_20261005/`.
- Regression tests cover dyads and six animals, shared/absent/ambiguous blobs,
  the inclusive 60-pixel boundary, stale proximity, missing-ID continuity and
  gaps, immediate/distant/brief raw returns, upstream swaps, input immutability,
  exported individual states/proximity, and release validation.

Use a new versioned output root for any subsequent video/PDF regeneration.
The old version-specific 25-run driver remains pinned to 1.5.2 and must not be
used as a 1.6.0 release driver. Future visual review should specifically check
missing-ID inference, since preserving raw assignments does not validate it.


## Regeneration and collaborator access (2026-10-05)

The previous statement that videos/PDFs were not regenerated is superseded: all 25 dyadic and 26 six-beetle runs are now COMPLETE_UNREVIEWED under PSC 1.6.0 / processor 0.8.2-group. Authoritative Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/psc_1_6_0_regenerated_51_20261005`. Local index: `outputs/psc_regenerated_51_20261005/review_set/START_HERE.html`. See `reports/PSC_1_6_0_REGENERATION_2026-10-05.md` for validation, sharing, and withdrawal receipts. Private Dropbox viewer access with downloads was granted to Hannah Donald and Charlotte Greene. Original inputs and provenance remain protected; historical release receipts are retained unchanged.
