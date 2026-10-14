# BA: a 100-run pilot with a focused marked viewer

Vince authorized a larger BA review after the five-clip check matched his submitted scores. This pilot uses 100 previously unused runs across 14 source recordings, plus a separate continuation of the previously scored A5 event. It freezes the current detector and keeps automatic suggestions distinct from human-confirmed posture. No new IDtracker jobs were needed: the pilot reuses matching existing tracking, and original videos, TOMLs, coordinates, earlier scores and releases remain unchanged.

**Current status: COMPLETE_UNREVIEWED.** All 100 new analyses, their videos/PDFs, the separate follow-up, and four portable review rounds are complete. `RELEASE_RECEIPT_v2.json` and the delivery verification record contain the checks; computational completion is not biological approval.

## What Vince will review

The detector suggests turtling in **22 of the 100 new runs**. **Ten runs have provisional QC flags**. Neither count establishes a behavioral diagnosis or an exclusion rule.

The focused reviewer contains 60 clips in four rounds:

| Round | Clips | Video time |
| --- | ---: | ---: |
| 1 | 10 | 9.37 minutes |
| 2 | 18 | 9.60 minutes |
| 3 | 14 | 9.54 minutes |
| 4 | 18 | 9.53 minutes |

Each round begins with a preselected complete run whose predictions are hidden. Other clips cover candidate boundaries and continuity, tracking/recovery concerns, and random eligible unflagged windows. Round 1 includes the earlier event's continuation at frames **7310–8738 inclusive**, overlapping 150 previously scored frames before extending through the remainder of its 7,200-frame analysis window. This is a follow-up, not a new independent case.

Short candidate bouts include context before and after. Long bouts contribute onset, midpoint and end scenes. Overlapping windows within a run are merged, and the final queue checks that a run's displayed windows do not overlap. In total there are four full runs, 49 candidate scenes, two additional QC scenes, four random unflagged controls and one prior-event follow-up. The video time is **38.03 minutes**, plus time for decisions and adjustments; review can stop after any round.

The viewer marks suggested frames in an orange timeline and reports the current candidate state below the video. Controls do not cover the beetle. It supports exact global-frame jumps, one-frame stepping, Correct / No turtling / Adjust / Unsure, browser saving, and a score download for each round. Space controls playback even when a decision button has focus, preventing an accidental decision on the next clip. Hidden controls have an explicit display rule. Recovery/reference uncertainty is displayed as uncertainty rather than as a negative detector finding.

Review the four complete clips before browsing the report collection: their predictions are hidden in the scoring interface and catalog rows, but the PDFs contain them. This is interface blinding, not a guarantee that a reviewer cannot access the predictions elsewhere.

## Selection, QC and interpretation

Seed **202610071** selected 100 runs from a pool of **161 unused eligible configurations**, using shuffled recording order and randomized runs within each recording. Allocation cycles across recordings until a recording runs out. It is recording-stratified sampling, not a simple random sample of all BA TOMLs. Source/session identity, ROI agreement, frame coverage and input hashes were verified again on Firebird. All 100 selected runs completed; none was silently replaced. Missing tracking and unconfirmed recovery were retained as QC cases rather than discarded.

These are new cells from recordings already represented in development. They provide a broader test across animals but are not a new-recording holdout. Candidate scenes are targeted; their agreement cannot estimate population-wide accuracy. The complete preselected runs and random unflagged controls help check for missed events. Scores approve only displayed frames, and unsure or unscored footage must not become negative labels. No flailing scoring is required.

The ten QC-flagged runs include eight from the known camera-bump recording, three with unconfirmed turtling recovery, two with no reliable prototype wake, and one each with high missing fraction, a long missing episode, missing baseline, or a high rejected-jump fraction. Flags overlap within runs. Camera displacement remains a known limitation: the user-confirmed frames 1098 and 1099 are supplied only for that recording, and there is no general camera-stabilization classifier.

## Outputs and frozen rules

Each completed run has original prototype movement summaries and frame data, the frozen experimental candidate and eligibility fields, QC records, a full 7,200-frame cropped video, a marked viewer, and source/code hashes. The 100 primary runs retain the prototype PDF pages with a new leading page for the frozen detector and QC. Baseline and revised candidate calculations are explicitly separated. Confirmed overturned seconds remain unassessed. Per-run ZIPs and a combined PDF collection provide reviewable outputs; the separate historical follow-up is not counted among the 100 new runs.

The scientific modules remain `ba_turtling_episode_experiment.py` **0.2.0-development** and `ba_turtling_recovery_gate.py` **0.1.0-development**, with the previously reviewed code snapshot and prototype processor **0.8.1**. The new execution/packaging driver is **0.1.1**. Its first smoke test found an unsupported optional PDF argument in the older frozen renderer. That failed attempt and the original driver are retained; the correction changed only the report call, and the completed outputs use a new `runs_v2/` directory. No detector rule was retuned.

The new scorer passed 27 software checks, including inclusive intervals, frame steps, unknown recovery, hidden predictions, incomplete/unsure handling, last-clip export, score import and keyboard behavior. These tests do not certify browser playback or behavior. Video frame counts, media hashes, PDF parsing, ZIP integrity and visual samples are checked separately in the release records.

Local working evidence: `outputs/ba_large_review_pilot_20261007/`.
Authoritative Firebird root: `/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_large_review_pilot_20261007`.

The next scientific step is to compare returned round scores with these frozen predictions, keeping guided and prediction-hidden results separate. The earlier 12 development runs still contain their documented disagreements; this larger automatic batch does not resolve them by itself. Exploratory dyadic testing is deferred so it does not delay this BA review. Dyadic fighting and occlusion need their own labels before transferring the BA interpretation. Social PSC and paused identity-editor work were not changed.

## Delivery version

The current portable review is `review_v2/START_HERE.html`; its four round files
contain their own videos. Full per-run ZIPs are in `individual_run_zips_v2/`.
The first packaging pass is retained as superseded, without replacing any
scientific result. The second pass uses integer-second seeking plus residual
frame trimming, and verifies exact source-frame alignment with decoded-pixel
tests, including H.264 sources. The combined `BA_Pilot_100_Reports.pdf` contains
600 pages with 100 run bookmarks. Each run's original report remains available
in its full Firebird bundle.

Setup PDF previews for BA001 and BA004 appeared in the chat during visual QA. Treat those two complete-run reviews as potentially
prediction-exposed when evaluating the returned labels; do not pool them into
a strictly blinded accuracy estimate. The preselected runs remain unchanged.

The six delivered files in `/Users/New/Downloads/BA_100_run_review_20261007/`
were read back and hash-verified: START_HERE, four scoring rounds, and the
combined report book. All 60 embedded media hashes matched their checked
MP4s, all four final scripts compiled, all index links resolved, and all 101
full-run videos have exactly 7,200 encoded frames. The 100 PDFs passed version
and frame-window checks; positive and high-missingness covers, plots and
metadata pages were visually inspected. Video samples decoded correctly at
the beginning, middle and end. Browser playback itself was not tool-tested.

`CURRENT_RELEASE.json` identifies the authoritative v2 paths. The earlier
packaging folders remain superseded evidence. `DOWNLOADS_DELIVERY.json`,
`LOCAL_PACKAGE_VERIFICATION.json`, `PDF_VERIFICATION.json`,
`FRAME_ALIGNMENT_TEST.json`, and `SCORER_TESTS.txt` retain the delivery checks.
