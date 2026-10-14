# Beetle tracking post-processing

This repository turns IDtracker.ai tracking into frame-by-frame beetle locations, movement and fungus measurements, review PDFs, and a synchronized video viewer. It supports dyads and larger groups with the **same persistent social contact (PSC) rules**. The original v0.8.1 prototype remains available for comparison; it is not the current PSC pipeline.

**Read the [visual project handoff](reports/PROJECT_HANDOFF_2026-09-28.html)** for a quick orientation, or the [text version](reports/PROJECT_HANDOFF_2026-09-28.md) for release paths and status. [AGENTS.md](AGENTS.md) is the concise technical handoff for the next development task.

| Current component | Version | Where it lives |
| --- | --- | --- |
| Persistent contact and pile model | **1.5.1** | `persistent_groups.py` |
| Shared group processor | **0.8.1-group** | `six_beetle_processor.py`, `group_processor.py` |
| Raw/PSC comparison viewer | **v3** | `build_canonical_review.py`, `interaction_review_template.html` |
| Outlined presumed tracks in PDF | **outlined-psc-v1** | `render_psc_outlined_pdf.py` |
| Historical standalone processor | 0.8.1 | `processor.py`, [legacy guide](docs/LEGACY_README_v0.8.1.md) |

The 2024 GroupTrial release has **26 six-beetle trials, 9,000 frames each**, starting at each TOML's own tracking start. The 2026 dyadic release has **99 eligible runs, 7,200 frames each**; one no-blob TOML and four structurally incompatible TOMLs were excluded. Both releases use PSC 1.5.1 and processor 0.8.1-group. Their code and parameter parity is documented in the release's `PROCESSOR_PARITY.json`. All automatic results remain **UNREVIEWED** until a person checks them against the video.

## Run a new analysis

Use a Python environment with the repository dependencies, the relevant IDtracker.ai environment, and `ffmpeg`/`ffprobe`. Start with `python group_firebird_gui.py` for the shared SSH-based interface, or `python dyadic_firebird_gui.py` for its dyad filter. `python idtracker_toml_gui.py` manages IDtracker TOML submissions. The GUI can deploy a hashed code snapshot and retrieve a verified bundle.

For a command-line run on an existing IDtracker session, see [GROUP_PIPELINE_README.md](GROUP_PIPELINE_README.md). The entry point is `python run_group_pipeline.py --help`; use a **new output directory**. Analysis windows use inclusive global frames. The scientific outputs are in frames and pixels. If you change the window, write a new versioned analysis; do not edit an existing release in place.

In the viewer, compare raw IDtracker locations with inferred PSC locations before accepting a result. A detected partner or compatible blob can support a pile location; when the evidence does not support a location, the beetle stays missing and earns no presumed distance or fungus occupancy. Review decisions export as a separate, hashed record; they do not rewrite source TOMLs or tracking.

## Find and interpret outputs

The release map and exact Firebird paths are in the [handoff report](reports/PROJECT_HANDOFF_2026-09-28.md). GroupTrial has a full ZIP and per-box ZIPs. Dyadic has a full ZIP and **99 individual run ZIPs**. Each run ZIP contains its HTML viewer, video, regular and outlined PDFs, frame-level CSVs, and provenance. Local `outputs/` is a working/download area, not the authoritative source, and is ignored by Git. A Dropbox path alone does not prove cloud upload or public access.

Use [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for columns and raw-versus-PSC meanings; [SIX_BEETLE_METHODS.html](SIX_BEETLE_METHODS.html) for detailed methods; and [CHANGELOG.md](CHANGELOG.md) for history. [REPOSITORY_STATUS.md](REPOSITORY_STATUS.md) explains the current versus historical code boundary.

## Verify the code

Run `venv-mac/bin/python -m unittest discover -s tests -v` on the Mac. The last local run on 2026-09-28 passed **133 tests**. These software checks do not establish that inferred identities or contacts are biologically correct. Preserve run manifests, version strings, source hashes, and human review status with every downstream table.

## BA scientific extraction checkpoint (14 October 2026)

VAF has selected 180 approved cells, including nine approved Savannah reruns; 41 cells are excluded. Four approved cells retain movement holds, leaving 176 without a movement hold. [Read the scientific data report](reports/BA_SCIENTIFIC_DATA_CHECKPOINT_2026-10-14.md) and [browse the approved versions](provenance/ba_science_selection_20261014/APPROVED_VIDEOS.html). The next outcomes are wall frames, fungus frames, movement latency in frames and total distance in pixels. Definitions and the extraction pilot come next; final outcome data have not yet been generated.
