# Persistent detection-supported groups — 2024 six-beetle battles

Six-beetle processor 0.6.1 uses persistent_groups.py (model 1.0.1) by default for every six-animal analysis. This is an unreviewed scientific estimate, not validated identity reconstruction. Original processor.py 0.8.1 and original trajectories remain intact.

Assigned beetles within 60 pixels remain visible proximity interactions. PSCP begins only when at least one member's identity is inferred from a shared detected blob. This corrects v0.6.0, which displayed internal groups as PSCP even when both beetles remained assigned.

A group follows detected blobs, retains membership when identities disappear, and has missing positions when there is no supporting detection. Separate branches require three consecutive consistent member assignments. Crucially, candidate branches move during confirmation; they are not constrained forever to the old pile center. Partial splits can release visible members while others remain unresolved. No frame-specific annotations enter the model. The 100 original-pixel/frame gate applies to detection continuity; reacquisition after a detection gap uses a fixed 60-pixel search radius.

The OLD reviewed episode, IDs 4–5 at frames 7229–7506, has supported shared positions in all 278 frames under the general algorithm, including frame 7340 when neither raw identity has coordinates. It is classified as PSCP for 277 frames and as a visible interaction for one frame. This does not prove all inferred identities. The earlier 2–5 episode has 211 PSCP frames and one visible-interaction frame within 216 reviewed frames; the remaining four frames are unsupported or separate. IDs 3–4 have 311 PSCP frames and 18 visible-interaction frames in the approximate 6700–7101 episode. Those disagreements remain unresolved; no claim of universal identity accuracy is made.

CSV movement and fungus calculations use the canonical path. During the OLD 4–5 interval, both beetles receive 1,096.93 pixels of movement, 168 F3 frames, and 409.82 pixels of F3 movement. A moving pile therefore contributes the same supported movement and fungus occupancy to each assigned pile member.

The first attempted persistent model over-retained members. It was rejected in full-session testing; adding moving branch confirmation recovered the 4–5 episode. All 89 existing/initial tests passed; an additional regression covers moving branches during confirmation. OLD canonical adjacent steps have maximum 89.24 px and zero steps over 100 px. Raw coordinates are retained as controls.

Each new bundle contains canonical_states.npz and canonical_positions.csv. estimated_windows.csv contains path-based movement summaries, and estimated_fungus_summary.csv contains fungus frame counts and fungus-specific distances. The report's estimated positions and fungus table use those same positions. The synchronized review reads the NPZ directly; it does not rerun a different inference model. Raw tables are explicitly separate controls. Reports cover each original analysis start through frame 16997, extending earlier 7200-interval reports so the entire reviewed fight is included. IDs remain zero-based (0–5), consistent with the existing viewer.

## Reuse

In the IDtracker environment, run export_blob_evidence.py SESSION to export detection evidence from preprocessing/list_of_blobs.pickle. In the postprocessing environment, use six_beetle_processor.py with the existing --trajectory, --session, --output, --start, --window, --video and --cell-label arguments. Blob evidence is required; missing evidence causes an explicit error. --blob-evidence can name a separate export. Existing output directories cannot be overwritten.

firebird_sweep/make_grid.py now packages the model and evidence exporter with new sweep jobs; run_task.py exports evidence before postprocessing. Existing queued/deployed jobs are not retroactively modified. Historical two-animal processor.py workflows remain separate. build_canonical_review.py accepts any six-beetle canonical bundle, a source video segment beginning at the analysis start, crop x/y/width/height in original pixels, and playback fps. Time in scientific outputs remains frames.

## Outputs

results/persistent_v061 contains OLD, OLD_TEst and MIX report bundles named after their source TOMLs. results/OLD_review_persistent_v061 contains the synchronized OLD review with 300-frame traces. Version 0.6.0 outputs are retained for provenance but superseded. All outputs require visual identity review before biological conclusions.
