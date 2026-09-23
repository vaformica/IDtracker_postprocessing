# Shared dyadic pipeline: Firebird validation on 2026 fight recording

The same group post-processor and HTML review used for the 2024 six-beetle
workflow ran on a real **two-beetle, one-fungus** IDtracker.ai session. This is
a software and provenance check, not an approval of inferred identities or
fighting behavior. All generated bundles remain `UNREVIEWED`.

## Source and runs

- Source session: `/data/labs/vformic1-swat-lab/2026_Videos/2026_Fights/2026_Fights_Recorded/session_Camera_1_40169154_20260701_1621_FIGHT_ACT2_C3_A00002_20260717_142007_ovn_auto`
- Source tracking interval: global frames `[118, 8046)`; IDtracker.ai records two animals and two ROIs (arena, fungus). Original video, session, and trajectories were read without modification.
- Firebird code snapshot: `/data/labs/vformic1-swat-lab/group_postprocessing_validation/_code/6745a5fe27deac86`; deployed file SHA-256 values matched the local files before the runs. Subsequent local changes to GUI search defaults, compact timeline presentation, and documentation do not alter the remote analyses.
- Slurm jobs: `898292` (frames 118–418: analysis, PDF, HTML, video), `898293` (frames 118–8045: full analysis/PDF/CSVs), and `898294` (frames 820–1120: contact-focused analysis, PDF, HTML, video). All completed successfully.

## Checks

- The first 301-frame bundle has 602 frame-data rows, one per beetle per frame. Its manifest hashes matched its outputs. Reaggregation of the saved frame data reproduced the fungus and pair summaries for that exact window.
- The contact-focused 301-frame bundle contains five frames of visible-identity proximity (833–837), followed by 283 frames of inferred shared position (838–1120). The portable HTML/video review showed the pair timeline, both positions, fungus/proximity/PSCP status, and 300-frame trails. Seeking to frame 850 and stepping to 851 kept the displayed frame and status synchronized; the browser reported no warnings or errors.
- The full 7,928-frame analysis produced 15,856 frame-data rows, a PDF, and pair/fungus/event summaries. Its pair table reports 16 visible-proximity frames and 7,202 presumed group frames. The exported frame data retain raw and canonical coordinates, source/status, inferred-group membership, fungus occupancy, and movement steps for later rewindowing.
- A read-only run of the GUI's actual Firebird discovery code found 569 two-animal/two-ROI sessions under the 2026 fights root. The local `group_firebird_gui.py` window instantiated with the `all` profile and that search root in its defaults.

## Scientific review needed

In this session, beetle 1 loses its independent IDtracker coordinate at frame
838. The persistent-group rule then assigns its inferred position to the
detected partner or shared blob through long intervals, including frames
838–4231 and 4322–8045. Raw ID 1 is present in only 715 of the 7,928 frames;
7,202 frames are labeled `PSCP_BLOB`. This follows the requested persistence
rule, but an inference lasting most of a recording cannot establish that the
two animals stayed together. Review source video and detection blobs across
those intervals before treating the inferred movement or fungus tallies as
biological results. The `location_source`, `inferred`, and raw-coordinate
columns allow these frames to be excluded or analyzed separately.

## Local artifacts

- First-window [PDF](../results/dyadic_generic_smoke_20260922/analysis/dyadic_smoke_20260922.pdf), [frame data](../results/dyadic_generic_smoke_20260922/analysis/frame_data.csv), and [portable HTML review](../results/dyadic_generic_smoke_20260922/review_final/interaction_review.html) (keep its adjacent MP4).
- Contact-focused [PDF](../results/dyadic_generic_smoke_20260922/pscp_run/analysis/dyadic_pscp_820_1120.pdf) and [portable HTML review](../results/dyadic_generic_smoke_20260922/pscp_run/review_final/interaction_review.html) (keep its adjacent MP4).
- Full-run [PDF](../results/dyadic_generic_smoke_20260922/full_run/analysis/dyadic_full_20260922.pdf), [frame data](../results/dyadic_generic_smoke_20260922/full_run/analysis/frame_data.csv), and [events](../results/dyadic_generic_smoke_20260922/full_run/analysis/events.csv).

Launch the shared Firebird interface with `python group_firebird_gui.py`, choose
`dyadic` (or `all`), search, select a session, inspect the inclusive frame range
and parameters, then submit. `python six_beetle_firebird_gui.py` opens the same
interface with the established six-beetle filter selected. The standalone
historical dyadic v0.8.1 processor remains a separate baseline; its outputs
are not silently mixed into these persistent-pile bundles.
