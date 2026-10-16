# Beetle tracking post-processing

**15 October 2026 dyadic handoff:** Vince, Hannah and Savannah judged the reviewed dyadic results acceptable to advance to broader fight processing and QC in the operations chat. The proposed variables, provenance fields, data dictionary and remaining definition decisions are in [the handoff README](reports/dyadic_handoff_20261015/README.md) and [PDF report](output/pdf/Dyadic_processing_handoff_and_data_dictionary_20261015.pdf). This is a proposed export schema, not a completed batch or a restart of six-beetle work.

**Current six-beetle status — 15 October 2026: ON HOLD.** Vince put six-beetle development on hold on October 14–15 because tracking is unreliable and correcting obscured piles takes too much time. Revisit when Charlotte needs network or time-on-fungus data; there is **no automatic October 19 or two-week restart**. Dyadic and BA work continue separately. Contact versus touching/mounting definitions remain deferred. See [Charlotte’s current handoff](SIX_BEETLE_README.md) for review limitations, sources, and the unresolved 26/28/30 count mapping.

**9 October 2026 encounter/orientation pilot:** Four synchronized reviews (two dyadic, two six-beetle) compare movement direction, undirected body axes, and contributions to approach/separation. This is a separate **UNREVIEWED** feasibility experiment; production defaults and source trajectories are unchanged. See [results, limitations, and viewer links](reports/ENCOUNTER_ORIENTATION_PILOT_2026-10-09.md).

**Paused identity correction pilot 0.3.0 (historical reference):** Box01 has an identity-only editor with bidirectional motion suggestions, raw-label comparison, and saved/preview correction intervals on the scrub timeline. Saved labels update playback immediately. See [pilot instructions and limitations](reports/IDENTITY_CORRECTOR_PILOT_2026-10-05.md). Exported decisions require reprocessing before downstream results change.

**5 October 2026 correction:** Hannah’s review exposed suppression of available IDtracker IDs in the shared dyadic/six-beetle engine. Development PSC **1.6.0** now preserves every available ID at its exact input position, restores returning IDs immediately, uses **60-pixel assigned-centroid proximity**, and permits PSC inference only for missing IDs. See [the correction and 51-run regression audit](reports/DYADIC_RAW_ID_PRIORITY_2026-10-05.md). All 25 dyadic and 26 six-beetle review sets have now been regenerated and verified. See [the current review collection and sharing record](reports/PSC_1_6_0_REGENERATION_2026-10-05.md).

**Dyadic withdrawal, 30 September 2026:** The audited 99-run PSC 1.5.1 derived output set and its earlier 1.5.1 copies have been deleted from Firebird and the local downloaded package at Vince’s request. Source videos, TOMLs, tracking, detection evidence, and provenance remain. References below to that release are historical. See `outputs/dyadic_withdrawal_20260930/` for deletion inventories and receipts. The replacement **25-run development pilot is complete and UNREVIEWED**; open `outputs/dyadic_pilot25_20260930/review_set/START_HERE.html` and see [its execution record](reports/DYADIC_PILOT25_2026-09-30.md). The exact reported episode still needs its cell/frame reference confirmed and is flagged for further review.

This repository turns IDtracker.ai tracking into frame-by-frame beetle locations, movement and fungus measurements, review PDFs, and a synchronized video viewer. It supports dyads and larger groups with the **same persistent social contact (PSC) rules**. The original v0.8.1 prototype remains available for comparison; it is not the current PSC pipeline.

**For the historical September checkpoint, read the [visual project handoff](reports/PROJECT_HANDOFF_2026-09-28.html)** for a quick orientation, or the [text version](reports/PROJECT_HANDOFF_2026-09-28.md) for release paths and status. [AGENTS.md](AGENTS.md) is the concise technical handoff for the next development task.

| Current component | Version | Where it lives |
| --- | --- | --- |
| Persistent contact and pile model | **1.6.0 (UNREVIEWED)** | `persistent_groups.py` |
| Shared group processor | **0.8.2-group** | `six_beetle_processor.py`, `group_processor.py` |
| Raw/PSC comparison viewer | **v4** | `build_canonical_review.py`, `interaction_review_template.html` |
| Outlined presumed tracks in PDF | **outlined-psc-v1** | `render_psc_outlined_pdf.py` |
| Historical standalone processor | 0.8.1 | `processor.py`, [legacy guide](docs/LEGACY_README_v0.8.1.md) |

The current collection contains **25 dyadic runs (7,200 inclusive frames each)** and **26 six-beetle trials (9,000 inclusive frames each)**. Both use PSC 1.6.0 and processor 0.8.2-group. The prior 99-run dyadic release was withdrawn; it was not rerun. The earlier 1.5.1 and 1.5.2 derived review files have been removed following a data-specific audit. Historical reports retain their original provenance.

All automatic results remain **UNREVIEWED**. Available IDtracker IDs retain their exact input positions, proximity uses a 60-pixel centroid radius, and only missing IDs can receive presumed social contact. Review HTML, MP4, PDF and package names identify the source video and TOML cell. See [current files and access instructions](reports/PSC_1_6_0_REGENERATION_2026-10-05.md).

## Run a new analysis

**BA refinement, 7 October:** Returned pilot scores led to a separate quiet-posture / circling experiment. See [before-and-after results and remaining limitations](reports/BA_TURTLING_CONTINUITY_REFINEMENT_2026-10-07.md). This is a development fit; the original pilot and production defaults are unchanged.

**BA development review, 7 October:** A 100-run pilot is complete and UNREVIEWED, with four portable marked-review rounds and the prototype reports. See [the pilot, checks and current download location](reports/BA_LARGE_REVIEW_PILOT_2026-10-07.md). Its frozen detector remains a posture hypothesis; returned scores and the separate refinement are documented above.

**BA single-animal pilot:** use `run_ba_pipeline.py` for one animal and one arena ROI, with 7,200 inclusive frames from the source TOML start. It retains the prototype BA calculations and PDF layout, adds synchronized video review and provisional QC flags, and does not use social PSC inference. See [BA_PIPELINE_README.md](BA_PIPELINE_README.md) for the pilot, output organization, and limitations.

Use a Python environment with the repository dependencies, the relevant IDtracker.ai environment, and `ffmpeg`/`ffprobe`. Start with `python group_firebird_gui.py` for the shared SSH-based interface, or `python dyadic_firebird_gui.py` for its dyad filter. `python idtracker_toml_gui.py` manages IDtracker TOML submissions. The GUI can deploy a hashed code snapshot and retrieve a verified bundle.

For a command-line run on an existing IDtracker session, see [GROUP_PIPELINE_README.md](GROUP_PIPELINE_README.md). The entry point is `python run_group_pipeline.py --help`; use a **new output directory**. Analysis windows use inclusive global frames. The scientific outputs are in frames and pixels. If you change the window, write a new versioned analysis; do not edit an existing release in place.

In the viewer, compare raw IDtracker locations with inferred PSC locations before accepting a result. A detected partner or compatible blob can support a pile location; when the evidence does not support a location, the beetle stays missing and earns no presumed distance or fungus occupancy. Review decisions export as a separate, hashed record; they do not rewrite source TOMLs or tracking.

## Find and interpret outputs

The [current collection record](reports/PSC_1_6_0_REGENERATION_2026-10-05.md) lists the authoritative Firebird location and private Dropbox review folder. Each case ZIP includes its linked HTML index, viewer, video, regular and outlined PDFs, CSV index, and provenance. Local `outputs/` is an ignored working copy. The older handoff describes historical releases, not the current downloadable files.

Use [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for columns and raw-versus-PSC meanings; [SIX_BEETLE_METHODS.html](SIX_BEETLE_METHODS.html) for detailed methods; and [CHANGELOG.md](CHANGELOG.md) for history. [REPOSITORY_STATUS.md](REPOSITORY_STATUS.md) explains the current versus historical code boundary.

The [BA boundary refinement and fresh scoring round](reports/BA_TURTLING_BOUNDARIES_AND_IMAGE_TEST_2026-10-07.md)
records the separate 0.4.0-development turtling experiment, rejected image-feature
trial, and nine-clip human check. It does not replace production defaults or establish
biological validation.

The [returned nine-clip scores](reports/BA_TURTLING_BOUNDARY_VALIDATION_RESULTS_2026-10-07.md)
show 1.11% disagreement on eight fresh clips, with an injury-associated false
event and a still-unresolved earlier onset in the separate follow-up. Keep these
results distinct from the earlier development fit.

## Verify the code

Run `venv-mac/bin/python -m unittest discover -s tests -v` on the Mac. The 2026-10-05 correction passed **157 tests**. These software checks do not establish that inferred identities or contacts are biologically correct. Preserve run manifests, version strings, source hashes, and human review status with every downstream table.

The [BA QC priorities and manual review dashboard](reports/BA_REVIEW_PRIORITIES_2026-10-12.md)
now covers 121 existing windows. It separates tracking problems, provisional
turtling uncertainty, human scoring coverage, and manual requests for more footage.

The [focused BA boundary follow-up](reports/BA_FOCUSED_BOUNDARY_RESULTS_2026-10-12.md)
identified a substantial missed on-back episode: the latest human onset is 3942,
while frozen 0.4 begins at 6910. This limits automatic duration estimates despite
the earlier small frame-error percentages. Original predictions and scores remain.

The [Firebird BA census](reports/BA_FIREBIRD_CENSUS_2026-10-12.md) separates missing
coordinates in the 121 reviewed windows from incomplete tracking/analysis coverage.
It lists configuration reconciliation and processing candidates without equating
copied TOMLs with independent animals or launching new tracking.

**Shared QC development, 12 October:** New BA and common dyadic/six-beetle pipeline
runs now include a review-only source-disturbance and tracking checker. It screens
every original video frame at reduced resolution, caches by source content, and
writes `unified_qc.html`/JSON with traces and scoped reasons. No automatic exclusions
or changes to scientific rules. See [the shared QC guide](UNIFIED_QC_README.md) and
[development evidence and limitations](reports/UNIFIED_QC_2026-10-12.md).

## BA scientific extraction checkpoint (14 October 2026)

VAF has selected 180 approved cells, including nine approved Savannah reruns; 41 cells are excluded. Four approved cells retain movement holds, leaving 176 without a movement hold. [Read the scientific data report](reports/BA_SCIENTIFIC_DATA_CHECKPOINT_2026-10-14.md) and [browse the approved versions](provenance/ba_science_selection_20261014/APPROVED_VIDEOS.html). The next outcomes are wall frames, fungus frames, movement latency in frames and total distance in pixels. Definitions and the extraction pilot come next; final outcome data have not yet been generated.

## Current fight dashboard screen — 16 October 2026

The operations fight dashboard uses the user-selected 300-frame candidate rule in `dyadic_turtling_long_bouts.py`; see [the integration report](reports/DYADIC_LONG300_DASHBOARD_2026-10-16.md). It is a separate review screen, not confirmed posture or a change to BA/shared processing defaults. The publication checkpoint retains accumulated BA, dyadic, turtling, review and dashboard work; paused work remains paused.
