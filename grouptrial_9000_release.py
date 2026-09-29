#!/usr/bin/env python3
"""Recompute the 21 reviewed GroupTrial trials for exactly 9,000 frames.

This creates a separate release. Original TOMLs, tracking, and longer reviews
are read-only inputs. The preserved first frame is the source TOML start frame;
the last analyzed global frame is start + 8999, inclusive.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


MODEL = "1.5.1"
PROCESSOR = "0.8.1-group"
VIEWER = "raw-psc-compare-v3"
PDF_STYLE = "outlined-psc-v1"
FRAMES = 9000
PYTHON = "/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python"
FFMPEG = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg"
FFPROBE = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe"
SOURCES = (
    ("original_11", "grouptrial_2024_pscp_v1_5_1_processor_0_8_1_release_20260924_2130utc"),
    ("additional_10", "grouptrial_2024_additional_psc_v1_5_1_processor_0_8_1_20260925_1337utc"),
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def atomic_json(path: Path, payload: dict) -> None:
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def source_rows(base: Path) -> tuple[list[dict], list[dict]]:
    rows, exclusions = [], []
    for cohort, name in SOURCES:
        source_root = base / name
        plan = read_json(source_root / "plan.json")
        exclusions.extend(plan.get("excluded", []))
        for task in plan["tasks"]:
            label = Path(task["source_toml"]).stem
            source_analysis = source_root / "tasks" / label / "analysis"
            meta = read_json(source_analysis / "manifest.json")
            settings = meta["settings"]
            start = int(task["start"])
            if start != int(settings["start"]):
                raise ValueError(f"Source start mismatch: {label}")
            if int(task["end_exclusive"]) - start < FRAMES:
                raise ValueError(f"Fewer than {FRAMES} source frames: {label}")
            if meta.get("persistent_model_version") != MODEL or meta.get("script_version") != PROCESSOR:
                raise ValueError(f"Wrong source analysis version: {label}")
            trajectory = Path(meta["trajectory_file"])
            session = Path(meta["session_folder"])
            video = Path(task["video"])
            source_toml = Path(task["source_toml"])
            if not all(p.is_file() for p in (trajectory, video, source_toml)) or not session.is_dir():
                raise FileNotFoundError(f"Source input missing: {label}")
            rows.append(dict(
                cohort=cohort, label=label, source_root=str(source_root),
                source_analysis_manifest=str(source_analysis / "manifest.json"),
                source_analysis_manifest_sha256=sha(source_analysis / "manifest.json"),
                source_toml=str(source_toml), source_toml_sha256=sha(source_toml),
                submitted_toml=task.get("submitted_toml"),
                source_video=str(video), trajectory=str(trajectory), session=str(session),
                first_global_frame=start, last_global_frame_inclusive=start + FRAMES - 1,
                analysis_frame_count=FRAMES,
                source_end_global_frame_inclusive=int(task["end_exclusive"]) - 1,
                fps=float(meta["frames_per_second"]),
                settings=settings,
            ))
    if len(rows) != 21 or len({row["label"] for row in rows}) != 21 or len(exclusions) != 7:
        raise ValueError("Expected exactly 21 unique analyzed trials and seven source exclusions")
    return rows, exclusions


def prepare(base: Path, destination: Path, code_source: Path) -> None:
    if destination.exists() and any((destination / name).exists() for name in ("plan.json", "tasks", "code")):
        raise FileExistsError(destination)
    rows, exclusions = source_rows(base)
    if not (code_source / "run_group_pipeline.py").is_file():
        raise FileNotFoundError(code_source)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(code_source, destination / "code")
    (destination / "tasks").mkdir()
    (destination / "logs").mkdir()
    manifest = dict(
        schema="grouptrial-9000-frame-plan-v1",
        created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        frame_convention="Global frames are zero-based and inclusive; each trial preserves its source start and ends at start+8999.",
        psc_model_version=MODEL, group_processor_version=PROCESSOR,
        review_view_version=VIEWER, pdf_track_style_version=PDF_STYLE,
        review_status="UNREVIEWED", frame_count=FRAMES,
        source_tomls_untouched=True, idtracker_tracking_untouched=True,
        tasks=rows, excluded_top_level_tomls=exclusions,
        code_sha256={p.name: sha(p) for p in (destination / "code").glob("*.py")},
    )
    atomic_json(destination / "plan.json", manifest)
    (destination / "README.md").write_text(
        "# GroupTrial 2024: exactly 9,000 frames per reviewed trial\n\n"
        "This is a separate 21-trial derivative of the PSC 1.5.1 / group processor "
        "0.8.1-group releases. Each trial begins at its original TOML start frame "
        "and contains exactly 9,000 observations, ending at start + 8,999 "
        "(inclusive). At 30 fps, this is 300 seconds; the encoded video rate is "
        "verified per output. Analysis is recomputed from the original IDtracker "
        "trajectory and blob evidence, so movement, fungus, contact, missingness, "
        "PDFs, frame-level CSVs, HTML overlays, and videos all use the same window. "
        "Source TOMLs, IDtracker results, and longer releases remain unchanged.\n\n"
        "`plan.json` records each global frame range, original analysis and source "
        "input. The seven top-level TOMLs excluded from the previous 21-run release "
        "remain excluded, with individual reasons in `excluded_top_level_tomls`. "
        "All PSC identities and biological interpretations are UNREVIEWED.\n"
    )
    print(json.dumps({"destination": str(destination), "tasks": len(rows), "exclusions": len(exclusions)}))


def video_stream(path: Path) -> dict:
    raw = subprocess.check_output([
        FFPROBE, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=nb_frames,r_frame_rate,avg_frame_rate",
        "-of", "json", str(path),
    ])
    return json.loads(raw)["streams"][0]


def run_one(root: Path, index: int) -> None:
    plan = read_json(root / "plan.json")
    row = plan["tasks"][index]
    label = row["label"]
    folder = root / "tasks" / label
    folder.mkdir(exist_ok=True)
    status = folder / "status.json"
    if status.exists():
        if read_json(status).get("stage") == "COMPLETE_UNREVIEWED":
            print(f"Already complete: {label}", flush=True)
            return
        raise FileExistsError(f"Existing incomplete task needs inspection: {status}")
    for name, expected in (("source_toml", row["source_toml_sha256"]),
                           ("source_analysis_manifest", row["source_analysis_manifest_sha256"])):
        if sha(Path(row[name])) != expected:
            raise ValueError(f"Input changed: {name}: {label}")
    if row["analysis_frame_count"] != FRAMES or row["last_global_frame_inclusive"] != row["first_global_frame"] + FRAMES - 1:
        raise ValueError(f"Invalid 9000-frame window: {label}")
    atomic_json(status, dict(stage="RUNNING", label=label, frame_count=FRAMES,
                             started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                             slurm_job_id=os.environ.get("SLURM_JOB_ID")))
    code = root / "code"
    command = [PYTHON, str(code / "run_group_pipeline.py"),
               "--session", row["session"], "--trajectory", row["trajectory"],
               "--source-toml", row["source_toml"], "--source-video", row["source_video"],
               "--analysis-output", str(folder / "analysis"),
               "--review-output", str(folder / "review"),
               "--start", str(row["first_global_frame"]),
               "--end", str(row["last_global_frame_inclusive"]),
               "--fps", str(row["fps"]), "--label", label,
               "--pdf-name", label + ".pdf",
               "--movement-threshold-px", str(row["settings"]["threshold"]),
               "--wall-buffer-px", str(row["settings"]["wall_buffer_px"]),
               "--fungus-buffer-px", str(row["settings"]["fungus_buffer_px"]),
               "--proximity-px", str(row["settings"]["social_distance_threshold_px"]),
               "--jump-threshold-px", str(row["settings"]["jump_threshold_px"]),
               "--idtracker-python", PYTHON, "--ffmpeg", FFMPEG, "--ffprobe", FFPROBE]
    group = read_json(Path(row["source_analysis_manifest"]))["persistent_group_settings"]
    for option, field in (("--reconstruction-speed-px", "max_step_px_per_frame"),
                          ("--split-confirmation-frames", "split_confirmation_frames"),
                          ("--gap-speed-px", "gap_speed_px_per_frame"),
                          ("--gap-radius-cap-px", "gap_radius_cap_px"),
                          ("--max-reacquire-gap-frames", "max_reacquire_gap_frames"),
                          ("--distant-confirmation-frames", "distant_confirmation_frames")):
        command += [option, str(group[field])]
    try:
        with (folder / "pipeline.log").open("x") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        meta = read_json(folder / "analysis" / "manifest.json")
        if (meta["persistent_model_version"] != MODEL or meta["script_version"] != PROCESSOR or
            int(meta["settings"]["start"]) != row["first_global_frame"] or
            int(meta["settings"]["window"]) != FRAMES - 1):
            raise ValueError(f"Wrong analysis version or window: {label}")
        from psc_release_validation import validate_bundle
        validate_bundle(folder / "analysis", MODEL, PROCESSOR)
        review_task = {"source_toml": row["source_toml"], "video": row["source_video"]}
        from rebuild_raw_psc_compare_reviews import rebuild_task
        # Viewer builder requires the completed status and source review receipt.
        atomic_json(status, dict(stage="COMPLETE_UNREVIEWED", label=label,
                                 phase="numerical_and_source_review", frame_count=FRAMES))
        rebuild_task(root, "grouptrial", review_task, FFMPEG)
        from render_psc_outlined_pdf import render
        render(folder / "analysis", folder / "pdf_outline_v1")
        stream = video_stream(folder / "review_compare_v3" / "review_video.mp4")
        if int(stream["nb_frames"]) != FRAMES:
            raise ValueError(f"Viewer frame count mismatch: {label}: {stream}")
        csv_path = folder / "analysis" / "frame_data.csv"
        with csv_path.open(newline="") as source:
            records = list(csv.DictReader(source))
        frames = {int(x["global_frame"]) for x in records}
        if frames != set(range(row["first_global_frame"], row["last_global_frame_inclusive"] + 1)):
            raise ValueError(f"Frame-data range mismatch: {label}")
        atomic_json(folder / "video_probe.json", stream)
        atomic_json(status, dict(stage="COMPLETE_UNREVIEWED", label=label,
                                 frame_count=FRAMES,
                                 first_global_frame=row["first_global_frame"],
                                 last_global_frame_inclusive=row["last_global_frame_inclusive"],
                                 review_video_frame_rate=stream.get("avg_frame_rate"),
                                 completed_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        print(f"COMPLETE {label}: {FRAMES} frames", flush=True)
    except Exception as exc:
        atomic_json(status, dict(stage="FAILED", label=label, error=repr(exc),
                                 failed_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        raise


def finalize(root: Path) -> None:
    plan = read_json(root / "plan.json")
    rows = []
    archive = root / "GroupTrial_2024_9000_frames_PSC_v1.5.1_processor0.8.1_21_reviews.zip"
    if archive.exists():
        raise FileExistsError(archive)
    for row in plan["tasks"]:
        label = row["label"]
        folder = root / "tasks" / label
        status = read_json(folder / "status.json")
        analysis = folder / "analysis"
        meta = read_json(analysis / "manifest.json")
        review = folder / "review_compare_v3"
        review_meta = read_json(review / "source_manifest.json")
        outline = folder / "pdf_outline_v1"
        outline_meta = read_json(outline / "render_manifest.json")
        video = review / "review_video.mp4"
        first = row["first_global_frame"]
        if (status.get("stage") != "COMPLETE_UNREVIEWED" or
            int(status.get("frame_count", -1)) != FRAMES or
            meta.get("persistent_model_version") != MODEL or
            meta.get("script_version") != PROCESSOR or
            meta.get("qc_status") != "UNREVIEWED" or
            int(meta["settings"]["start"]) != first or
            int(meta["settings"]["window"]) != FRAMES - 1 or
            review_meta.get("review_view_version") != VIEWER or
            review_meta.get("analysis_manifest_sha256") != sha(analysis / "manifest.json") or
            int(review_meta.get("analysis_frame_count", -1)) != FRAMES or
            review_meta.get("copied_video_sha256") != sha(video) or
            outline_meta.get("psc_model_version") != MODEL or
            outline_meta.get("processor_version") != PROCESSOR or
            outline_meta.get("pdf_track_style_version") != PDF_STYLE or
            outline_meta.get("source_manifest_sha256") != sha(analysis / "manifest.json") or
            outline_meta.get("pdf_sha256") != sha(outline / outline_meta["pdf_filename"])):
            raise ValueError(f"Version, hash, or window mismatch: {label}")
        stream = video_stream(video)
        if int(stream["nb_frames"]) != FRAMES:
            raise ValueError(f"Encoded review has {stream['nb_frames']} frames: {label}")
        with (analysis / "frame_data.csv").open(newline="") as source:
            frames = {int(record["global_frame"]) for record in csv.DictReader(source)}
        if frames != set(range(first, first + FRAMES)):
            raise ValueError(f"Frame CSV does not have exactly the analysis interval: {label}")
        rows.append(dict(label=label, cohort=row["cohort"], source_toml=row["source_toml"],
                         first_global_frame=first, last_global_frame_inclusive=first + FRAMES - 1,
                         analyzed_frame_count=FRAMES,
                         video_nb_frames=int(stream["nb_frames"]),
                         video_avg_frame_rate=stream.get("avg_frame_rate"),
                         video_r_frame_rate=stream.get("r_frame_rate"),
                         video_sha256=sha(video), analysis_manifest_sha256=sha(analysis / "manifest.json"),
                         outlined_pdf_sha256=outline_meta["pdf_sha256"]))
    if len(rows) != 21:
        raise ValueError(f"Expected 21 complete trials, got {len(rows)}")
    with (root / "run_manifest.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    release = dict(schema="grouptrial-9000-frame-release-v1",
                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   frame_count_per_trial=FRAMES, trial_count=21,
                   psc_model_version=MODEL, group_processor_version=PROCESSOR,
                   viewer_version=VIEWER, pdf_style_version=PDF_STYLE,
                   review_status="UNREVIEWED", source_tracking_untouched=True,
                   source_tomls_untouched=True, plan_sha256=sha(root / "plan.json"),
                   runner_sha256=sha(root / "grouptrial_9000_release.py"),
                   run_manifest_sha256=sha(root / "run_manifest.csv"),
                   source_exclusion_count=7)
    atomic_json(root / "VERSION_CONTROL.json", release)
    with zipfile.ZipFile(archive, "w", allowZip64=True) as target:
        for name in ("README.md", "plan.json", "run_manifest.csv", "VERSION_CONTROL.json"):
            target.write(root / name, name)
        for row in plan["tasks"]:
            folder = root / "tasks" / row["label"]
            for name, source in (("source.toml", Path(row["source_toml"])),
                                 ("submitted.toml", Path(row["submitted_toml"]))):
                if source.is_file():
                    target.write(source, f"{row['label']}/{name}")
            for subdir in ("analysis", "review_compare_v3", "pdf_outline_v1"):
                for source in sorted((folder / subdir).iterdir()):
                    if not source.is_file():
                        continue
                    method = zipfile.ZIP_STORED if source.suffix in (".mp4", ".pdf", ".npz") else zipfile.ZIP_DEFLATED
                    target.write(source, f"{row['label']}/{subdir}/{source.name}", compress_type=method)
            for name in ("status.json", "analysis.pipeline_receipt.json", "video_probe.json"):
                source = folder / name
                if source.is_file():
                    target.write(source, f"{row['label']}/{name}")
    with zipfile.ZipFile(archive) as target:
        bad = target.testzip()
        if bad is not None:
            raise ValueError(f"Corrupt ZIP member: {bad}")
    release["archive"] = str(archive)
    release["archive_sha256"] = sha(archive)
    release["archive_bytes"] = archive.stat().st_size
    atomic_json(root / "RELEASE_RECEIPT.json", release)
    print(json.dumps(release, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("base", type=Path)
    p.add_argument("destination", type=Path)
    p.add_argument("code_source", type=Path)
    r = sub.add_parser("run")
    r.add_argument("root", type=Path)
    r.add_argument("index", type=int)
    f = sub.add_parser("finalize")
    f.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.base, args.destination, args.code_source)
    elif args.mode == "run":
        sys.path.insert(0, str(args.root / "code"))
        run_one(args.root, args.index)
    else:
        finalize(args.root)


if __name__ == "__main__":
    main()
