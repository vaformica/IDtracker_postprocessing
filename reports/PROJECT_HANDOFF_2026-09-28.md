# Beetle tracking pipeline · project handoff
**Checkpoint: 28 September 2026 · current automatic releases are UNREVIEWED**

## What this project does

IDtracker.ai supplies tracked coordinates and detection evidence. This post-processor keeps the raw coordinates beside a second, explicitly inferred PSC path. When beetles plausibly overlap in a pile, an unseen beetle can share a detected partner or compatible blob location. If the evidence is insufficient, its location remains missing. The processor then measures movement, proximity, fungus occupancy, and uncertainty frame by frame. A PDF and synchronized video let a researcher compare the inference with the original recording.

The code supports **two or more beetles** and an arena plus **one or more fungus ROIs**. The 2024 group videos use six beetles and three fungus ROIs. Fungus numbering follows the input ROI order; the group trial ROIs are ordered left to right in their normalized review orientation. The 2026 fight videos use two beetles. Both use the **same PSC 1.5.1 core and parameters**, demonstrated by the release's `PROCESSOR_PARITY.json`; different data can still produce different contact classifications.

## The current releases

| Collection | Analysis window | What is available | Scientific status |
| --- | --- | --- | --- |
| **2024 GroupTrial** | 26 six-beetle trials; 9,000 frames each, beginning at each TOML tracking start | Full ZIP and 26 per-box ZIPs; paired raw/PSC tables, frame data, HTML/video, regular and outlined PDFs | **UNREVIEWED** |
| **2026 dyadic fights** | 99 eligible configurations; 7,200 frames each, beginning at each TOML tracking start | Full ZIP and 99 per-run ZIPs with the same review materials | **UNREVIEWED** |

For dyadic fights, four structurally incompatible TOMLs were excluded before the eligible plan and one additional TOML yielded no IDtracker blobs. Their exclusion records are retained; no missing PDF was fabricated. GroupTrial contains 21 earlier trials plus five newly tracked corrected TOMLs. Both release ZIPs passed integrity checks. A passing package check establishes completeness and provenance, not that every ID is biologically correct.

### Firebird locations

**GroupTrial root**

```text
/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/grouptrial_2024_9000_frames_OFFICIAL_26_psc_v1_5_1_processor_0_8_1_20260928
```

Full ZIP: `GroupTrial_2024_OFFICIAL_26_9000frames_PSC_v1.5.1_processor0.8.1.zip`
SHA-256: `3b05174855d82efe619116e2a14876ba5ddf8b7953cc74c47928f42a77ab2c4f`
Per-box ZIPs: `by_box/` (26). The full and per-box ZIPs were also copied into local `outputs/grouptrial_2024_9000_official_26/`; that path being under Dropbox storage does **not** by itself confirm cloud sync or a public download link.

**Dyadic root**

```text
/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_fight_7200_frames_psc_v1_5_1_processor_0_8_1_20260928
```

Full ZIP: `Dyadic_2026_99_7200frames_PSC_v1.5.1_processor0.8.1.zip`
SHA-256: `2064ff0d95b2774da35f94122080d7842d02ae7f25f413aa88bb5cc76524f66b`
Individual ZIPs: `individual_run_zips/` (99). Find a run in `ZIP_INDEX.csv`, then download only its ZIP via Firebird SSH/SFTP. The 7.66 GB full ZIP was deliberately left on Firebird because of local disk space.

The two ZIP formats are *collections*. Each per-run package contains the HTML viewer beside its MP4, both PDFs, frame-level and summary CSVs, source/submitted TOML information, and run provenance. Do not mistake the separate `individual_videos/` directory for complete analysis bundles.

## How an analysis is built

```text
source video + source TOML
            ↓
IDtracker.ai tracking + detection evidence
            ↓
shared PSC 1.5.1 model  →  raw coordinates retained
            ↓
0.8.1-group frame data + summaries + regular/outlined PDFs
            ↓
raw-versus-PSC viewer v3 + synchronized video
            ↓
human review log → separate reviewed output, if approved by a researcher
```

The PSC path is a **hypothesis about location**, not a second IDtracker observation. The model uses contact, compatible detection blobs, individual movement constraints and sustained reidentification. A split or identity conflict can remain unresolved; those frames have no credited PSC path length or fungus time. Conversely, when a moving pile has a supported location, its inferred members can accrue PSC distance and fungus occupancy. The raw and PSC measurements stay separate in `frame_data.csv`, `window_comparison.csv`, `region_comparison.csv`, and `fungus_comparison.csv`. [The data dictionary](../DATA_DICTIONARY.md) defines each field and denominator.

The video viewer switches between raw IDtracker and analyzed PSC positions. Presumed paths are visually distinct, and the PDFs outline PSC portions of tracks. The group Box 3 videos are rotated for review without changing analytic coordinates. Timeline flags invite checking missing beetles, conflicts, proximity, and inferred pile members. A reviewer can export attributed corrections, then apply them to a **new** bundle; automatic source results stay intact.

## Start the next run

1. Read the source TOML, confirm beetle count, arena/fungus ROI order and tracking start, and decide the inclusive analysis frame window.
2. Use `python group_firebird_gui.py` for any supported group, `python dyadic_firebird_gui.py` for a dyad-filtered view, or `python idtracker_toml_gui.py` to submit IDtracker TOMLs. The CLI is [documented here](../GROUP_PIPELINE_README.md) and exposes `python run_group_pipeline.py --help`.
3. Write to a **new versioned output folder**. Confirm the run manifest records PSC model **1.5.1**, group processor **0.8.1-group**, parameters, source hashes, viewer **v3**, PDF style **outlined-psc-v1**, and `UNREVIEWED`.
4. Verify frame/animal row counts, encoded MP4 frame counts, both PDFs, raw/PSC comparisons and ZIP integrity. Then inspect flagged passages in the viewer before accepting quantitative conclusions.

Local test command: `venv-mac/bin/python -m unittest discover -s tests -v`; **133 tests passed** on 28 September. The old `processor.py` with `VERSION=0.8.1` is a historical standalone route. Use the shared group code for future PSC work. [Technical future-self notes](../AGENTS.md) identify the current files and release receipts.

## What is still open

These are **ready for human review**, not labeled ground truth. The most valuable next step is to review representative piles, identity conflicts, split/return episodes, and raw-versus-PSC disagreements, then record attributed edits. Releasing a different PSC algorithm requires a new model version and fresh outputs; changing only the frame window likewise requires a new versioned analysis. Old automatic data should never be silently mixed with a new release.

Firebird paths are SSH/SFTP locations, not public URLs. Shared Dropbox or Globus access was not verified at this checkpoint. The lab notebook's Charlotte data tab records the same stopping point.
