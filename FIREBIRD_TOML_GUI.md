# Firebird IDtracker.ai TOML manager

Run the local GUI from this repository with:

```bash
./venv-mac/bin/python idtracker_toml_gui.py
```

The Mac is only a client. The GUI searches Firebird over SSH, reads TOMLs, and submits IDtracker.ai to Slurm on Firebird. It does not mount Firebird or copy the source videos to the Mac.

## Normal workflow

1. Connect the Mac to the Swarthmore VPN.
2. Start the GUI and click **Test SSH**.
3. Click **Search TOMLs**. The default search root is Charlotte's `Groupagetrial_2024` folder.
4. Start with **Eligible originals**. This shows top-level TOMLs whose parsed inputs specify six animals and exactly four ROIs: one arena and three fungus ROIs.
5. Select a TOML to see its common inputs. The **Raw TOML** tab exposes every input, including the full ROI polygons.
6. Change the common fields and click **Apply common inputs to raw TOML**, or edit the raw TOML directly and click **Validate and stage**.
7. Select one or more eligible TOMLs and use **Preview selected** before **Submit selected to IDtracker.ai**.
8. Use **Load managed runs** and **Refresh selected** to revisit jobs after restarting the GUI.

The background-subtraction checkbox now follows each selected TOML. Merely typing in the raw editor creates a draft; the GUI blocks submission until **Validate and stage** is clicked. **Preview selected** lists any staged thresholds, background mode, and start frame. Submission receipts record whether the submitted copy came from the unchanged source, the common-input form, or a validated raw edit.

## Paired recovery and comparison (22 September 2026)

`run_paired_firebird.py --submit` pins the five original 2024 GroupTrial TOMLs that lacked trajectories in the first managed batch by SHA-256. It makes two separate background-subtracted runs per source: original human thresholds and area, and the provisional shared 50–255 intensity / 400.0 px² minimum area setting. The source TOMLs, four ROIs, and each individual start/end frame are preserved. The original MIX threshold with background enabled is a deliberate control and may perform poorly; it is not a recommended operating setting. The jobs request Quadro 8000 GPUs on `gpu02` because the four prior no-output jobs encountered uncorrectable ECC errors on `gpu04`.

The companion `compare_paired_firebird.py results/paired_20260922_004953_utc` writes `runs.csv`, `pairs.csv`, and `COMPARISON.md` from actual trajectory files. It reports raw missing coordinates, per-beetle missingness, all-six-present frames, IDtracker's estimated identity accuracy, and adjacent jumps. Failed or unfinished runs remain unscored. These are tracking-quality measures, before presumed social contact reconstruction; visual review of identity continuity is still needed.

## Run the six-beetle processor

Wait until the managed job reports `COMPLETE_UNREVIEWED`. Select it and click **Open post-processing GUI**. In the processor window:

1. Click **Find six-beetle sessions**. The managed IDtracker run folder is already included in the default search roots.
2. Select the completed session. Confirm the source video, global start and inclusive end frames, and the proximity, jump, and reconstruction settings.
3. Click **Preview exact Firebird command** to review the complete command and destination.
4. Click **Submit complete pipeline**. This runs the six-beetle processor and creates the CSV tables, PDF, interactive HTML review, and synchronized review video.
5. Use **Check latest job** until it finishes, then **Download latest bundle**.

The tracking job and post-processing job remain separate on purpose. A completed IDtracker job is still unreviewed, and changing post-processing thresholds does not require rerunning IDtracker.ai.

## Provenance and safety

Source TOMLs are read-only. Each submission creates a new timestamped folder under `managed_idtracker_runs` containing:

- `input/submitted.toml`, the exact submitted version;
- `submission_request.json`, with the source and submitted SHA-256 hashes, command, environment, and Slurm resources;
- `submission_receipt.json`, adding the Slurm job ID;
- `status.json`, written atomically as the job moves through `TRACKING`, `COMPLETE_UNREVIEWED`, or `FAILED`;
- `idtracker.log` and `slurm-<job>.log`;
- `idtracker_output/`, which contains the IDtracker.ai session output.

The submitter refuses TOMLs unless they parse successfully, specify six animals and four ROIs, and reference video paths that exist on Firebird. Completed tracking remains **UNREVIEWED** until the trajectory and downstream reports have been checked.

The job table checks for a real six-animal trajectory before declaring an output ready. It distinguishes invalid TOML files, GPU ECC failures, and runs where IDtracker.ai returned an error code after writing usable trajectories (`OUTPUT_READY_WITH_EXIT_WARNING`). The latter still require normal trajectory review before post-processing.

The defaults reproduce the successful six-beetle Firebird jobs: the `firebird` SSH alias, the `idtrackerai_6_0_14` environment, an L40S GPU, 16 CPUs, 64 GB RAM, and an eight-hour limit.
