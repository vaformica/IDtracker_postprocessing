#!/usr/bin/env python3
"""Create a separate, exactly 7,200-frame 2026 dyadic PSC release.

The original IDtracker trajectories and TOMLs are read-only. Each analysis
starts at that TOML's tracking start S and ends at S+7,199 inclusive.
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
import tomllib
import zipfile

FRAMES = 7200
MODEL = "1.5.1"
PROCESSOR = "0.8.1-group"
VIEWER = "raw-psc-compare-v3"
PDF_STYLE = "outlined-psc-v1"
PYTHON = "/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python"
FFMPEG = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg"
FFPROBE = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, data: dict) -> None:
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    partial.replace(path)


def probe(path: Path) -> dict:
    raw = subprocess.check_output([FFPROBE, "-v", "error", "-select_streams", "v:0",
                                   "-show_entries", "stream=nb_frames,r_frame_rate,avg_frame_rate",
                                   "-of", "json", str(path)])
    return json.loads(raw)["streams"][0]


def prepare(source: Path, destination: Path, code_source: Path) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    old_plan = read(source / "plan.json")
    tasks = []
    for task in old_plan["tasks"]:
        old = source / "tasks" / task["id"]
        excluded = (old / "final_status.json").is_file() and read(old / "final_status.json").get("stage") == "EXCLUDED_TRACKING_NO_BLOBS"
        row = dict(id=task["id"], source_path=task["source_path"],
                   source_sha256=task["source_sha256"], excluded=excluded)
        submitted_path = old / "input" / "submitted.toml"
        submitted = tomllib.loads(submitted_path.read_text())
        start, original_end_exclusive = map(int, submitted["tracking_intervals"][0])
        row.update(first_global_frame=start, last_global_frame_inclusive=start+FRAMES-1,
                   original_end_exclusive=original_end_exclusive,
                   submitted_sha256=sha(submitted_path), source_task=str(old))
        if not excluded:
            old_status = read(old / "status_v151r081.json")
            old_manifest_path = old / "analysis_v151r081" / "manifest.json"
            old_manifest = read(old_manifest_path)
            if (old_status.get("stage") != "COMPLETE_UNREVIEWED" or
                    old_manifest.get("persistent_model_version") != MODEL or
                    old_manifest.get("script_version") != PROCESSOR or
                    int(old_manifest["settings"]["start"]) != start or
                    int(old_manifest["settings"]["window"]) + 1 < FRAMES or
                    original_end_exclusive - start < FRAMES):
                raise ValueError(f"Not enough validated source frames: {task['id']}")
            session = Path(old_manifest["session_folder"])
            trajectory = Path(old_manifest["trajectory_file"])
            video = Path(submitted["video_paths"][0])
            if not (session.is_dir() and trajectory.is_file() and video.is_file()):
                raise FileNotFoundError(f"Missing tracking/video: {task['id']}")
            row.update(session=str(session), trajectory=str(trajectory), source_video=str(video),
                       original_analysis_manifest=str(old_manifest_path),
                       original_analysis_sha256=sha(old_manifest_path),
                       trajectory_sha256=sha(trajectory), fps=float(old_manifest["frames_per_second"]),
                       settings=old_manifest["settings"],
                       persistent_group_settings=old_manifest["persistent_group_settings"])
        tasks.append(row)
    if sum(not x["excluded"] for x in tasks) != 99 or sum(x["excluded"] for x in tasks) != 1:
        raise ValueError("Expected 99 eligible tasks and one documented no-blob exclusion")
    destination.mkdir(parents=True)
    shutil.copytree(code_source, destination / "code")
    (destination / "tasks").mkdir()
    (destination / "logs").mkdir()
    for row in tasks:
        out = destination / "tasks" / row["id"]
        (out / "input").mkdir(parents=True)
        old = Path(row["source_task"])
        for name in ("source.toml", "submitted.toml"):
            shutil.copy2(old / "input" / name, out / "input" / name)
        shutil.copy2(old / "task.json", out / "task.json")
        if row["excluded"]:
            shutil.copy2(old / "final_status.json", out / "final_status.json")
            for log in old.glob("idtracker_attempt_*.log"):
                shutil.copy2(log, out / log.name)
    plan = dict(schema="dyadic-2026-7200-frame-plan-v1",
                created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                frame_rule="For each TOML start S, analyze global frames S through S+7199 inclusive.",
                frame_count=FRAMES, psc_model_version=MODEL,
                group_processor_version=PROCESSOR, review_view_version=VIEWER,
                pdf_track_style_version=PDF_STYLE, review_status="UNREVIEWED",
                source_tomls_untouched=True, idtracker_tracking_untouched=True,
                source_batch=str(source), tasks=tasks,
                source_plan_sha256=sha(source / "plan.json"),
                code_sha256={p.name: sha(p) for p in (destination / "code").glob("*.py")})
    write(destination / "plan.json", plan)
    (destination / "README.md").write_text(
        "# 2026 dyadic fights: exactly 7,200 frames per eligible trial\n\n"
        "Each analysis starts at its own immutable submitted TOML tracking start S "
        "and includes S through S+7,199 inclusive. This is a separate derivative "
        "of the existing IDtracker trajectories: no tracking was rerun. Every raw/PSC "
        "table, per-frame CSV, quality metric, PDF, HTML overlay and encoded review "
        "video is recomputed for this same window. PSC model 1.5.1, group processor "
        "0.8.1-group, RAW/PSC viewer v3 and outlined-PSC PDFs are retained. "
        "Ninety-nine eligible configurations are included; the one no-blob run "
        "is explicitly excluded. Four structurally incompatible source TOMLs were "
        "excluded in the original batch plan. All results are UNREVIEWED. "
        "IDtracker identity scores are internal scores, not calibrated correctness probabilities.\n"
    )
    print(json.dumps({"destination": str(destination), "eligible": 99, "no_blob_excluded": 1}), flush=True)


def run_one(root: Path, index: int) -> None:
    plan = read(root / "plan.json")
    row = plan["tasks"][index]
    folder = root / "tasks" / row["id"]
    if row["excluded"]:
        print(f"EXCLUDED_NO_BLOBS {row['id']}", flush=True)
        return
    status = folder / "status_v151r081.json"
    if status.exists():
        if read(status).get("stage") == "COMPLETE_UNREVIEWED":
            print(f"Already complete: {row['id']}", flush=True)
            return
        raise FileExistsError(f"Inspect incomplete output before retry: {folder}")
    if (sha(Path(row["source_path"])) != row["source_sha256"] or
            sha(folder / "input" / "submitted.toml") != row["submitted_sha256"] or
            sha(Path(row["original_analysis_manifest"])) != row["original_analysis_sha256"] or
            sha(Path(row["trajectory"])) != row["trajectory_sha256"]):
        raise ValueError(f"Input changed: {row['id']}")
    start = row["first_global_frame"]
    end = row["last_global_frame_inclusive"]
    if end - start + 1 != FRAMES:
        raise ValueError("Window is not exactly 7,200 observations")
    code = Path(__file__).resolve().parent
    old = read(Path(row["original_analysis_manifest"]))
    settings = row["settings"]
    group = row["persistent_group_settings"]
    if settings != old["settings"] or group != old["persistent_group_settings"]:
        raise ValueError("Source analysis parameters changed")
    submitted = tomllib.loads((folder / "input" / "submitted.toml").read_text())
    analysis = folder / "analysis_v151r081"
    review = folder / "review_v151r081"
    quality = folder / "quality_v151r081.json"
    command = [PYTHON, str(code / "run_group_pipeline.py"),
               "--session", row["session"], "--trajectory", row["trajectory"],
               "--source-toml", row["source_path"], "--source-video", row["source_video"],
               "--analysis-output", str(analysis), "--review-output", str(review),
               "--start", str(start), "--end", str(end), "--fps", str(row["fps"]),
               "--label", str(submitted.get("name") or old.get("cell_label") or row["id"]),
               "--pdf-name", row["id"] + ".pdf",
               "--movement-threshold-px", str(settings["threshold"]),
               "--wall-buffer-px", str(settings["wall_buffer_px"]),
               "--fungus-buffer-px", str(settings["fungus_buffer_px"]),
               "--proximity-px", str(settings["social_distance_threshold_px"]),
               "--jump-threshold-px", str(settings["jump_threshold_px"]),
               "--idtracker-python", PYTHON, "--ffmpeg", FFMPEG, "--ffprobe", FFPROBE]
    for option, field in (("--reconstruction-speed-px", "max_step_px_per_frame"),
                          ("--split-confirmation-frames", "split_confirmation_frames"),
                          ("--gap-speed-px", "gap_speed_px_per_frame"),
                          ("--gap-radius-cap-px", "gap_radius_cap_px"),
                          ("--max-reacquire-gap-frames", "max_reacquire_gap_frames"),
                          ("--distant-confirmation-frames", "distant_confirmation_frames")):
        command.extend((option, str(group[field])))
    write(status, dict(stage="RUNNING", utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                       slurm_job_id=os.environ.get("SLURM_JOB_ID"), interval_inclusive=[start, end],
                       trajectory_sha256=row["trajectory_sha256"], command=command))
    try:
        with (folder / "pipeline.log").open("x") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        from psc_release_validation import validate_bundle
        meta = read(analysis / "manifest.json")
        if (meta["persistent_model_version"] != MODEL or meta["script_version"] != PROCESSOR or
                int(meta["settings"]["start"]) != start or
                int(meta["settings"]["window"]) != FRAMES-1):
            raise ValueError("Analysis manifest version/window mismatch")
        validate_bundle(analysis, MODEL, PROCESSOR)
        from dyadic_quality import summary
        quality.write_text(json.dumps(summary(analysis, Path(row["session"]),
                                              row["source_path"], row["source_sha256"]),
                                      indent=2, allow_nan=False) + "\n")
        write(status, dict(stage="COMPLETE_UNREVIEWED", phase="numerical_and_source_review",
                           interval_inclusive=[start, end], frame_count=FRAMES))
        from rebuild_raw_psc_compare_reviews import rebuild_task
        rebuild_task(root, "dyadic", row, FFMPEG)
        from render_psc_outlined_pdf import render
        render(analysis, folder / "pdf_outline_v1")
        stream = probe(folder / "review_compare_v151r081_v3" / "review_video.mp4")
        if int(stream["nb_frames"]) != FRAMES:
            raise ValueError(f"Review video has {stream['nb_frames']} frames")
        write(folder / "video_probe.json", stream)
        write(status, dict(stage="COMPLETE_UNREVIEWED",
                           utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                           slurm_job_id=os.environ.get("SLURM_JOB_ID"),
                           interval_inclusive=[start, end], frame_count=FRAMES,
                           analysis=str(analysis), review=str(folder / "review_compare_v151r081_v3"),
                           outlined_pdf=str(folder / "pdf_outline_v1"), quality=str(quality)))
    except BaseException as error:
        write(status, dict(stage="FAILED", utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                           slurm_job_id=os.environ.get("SLURM_JOB_ID"), error=repr(error)))
        raise


def finalize(root: Path) -> None:
    plan = read(root / "plan.json")
    rows = []
    quality_rows = []
    for task in plan["tasks"]:
        if task["excluded"]:
            continue
        folder = root / "tasks" / task["id"]
        analysis = folder / "analysis_v151r081"
        review = folder / "review_compare_v151r081_v3"
        outline = folder / "pdf_outline_v1"
        state = read(folder / "status_v151r081.json")
        meta = read(analysis / "manifest.json")
        viewer = read(review / "source_manifest.json")
        pdf = read(outline / "render_manifest.json")
        video = review / "review_video.mp4"
        first = task["first_global_frame"]
        if (state.get("stage") != "COMPLETE_UNREVIEWED" or state.get("frame_count") != FRAMES or
                meta.get("persistent_model_version") != MODEL or meta.get("script_version") != PROCESSOR or
                int(meta["settings"]["start"]) != first or int(meta["settings"]["window"]) != FRAMES-1 or
                viewer.get("review_view_version") != VIEWER or
                viewer.get("analysis_frame_count") != FRAMES or
                viewer.get("analysis_manifest_sha256") != sha(analysis / "manifest.json") or
                viewer.get("copied_video_sha256") != sha(video) or
                pdf.get("pdf_track_style_version") != PDF_STYLE or
                pdf.get("source_manifest_sha256") != sha(analysis / "manifest.json") or
                pdf.get("pdf_sha256") != sha(outline / pdf["pdf_filename"])):
            raise ValueError(f"Failed provenance/version/window gate: {task['id']}")
        for pdf_path in (analysis / meta["pdf_filename"], outline / pdf["pdf_filename"]):
            pdf_text = subprocess.check_output(["pdftotext", str(pdf_path), "-"], text=True)
            if MODEL not in pdf_text or PROCESSOR not in pdf_text:
                raise ValueError(f"PDF does not visibly state PSC/processor versions: {pdf_path}")
        from psc_release_validation import validate_bundle
        if validate_bundle(analysis, MODEL, PROCESSOR)["frames"] != FRAMES:
            raise ValueError(f"Wrong canonical frame count: {task['id']}")
        stream = probe(video)
        if int(stream["nb_frames"]) != FRAMES:
            raise ValueError(f"Wrong encoded review frame count: {task['id']}")
        with (analysis / "frame_data.csv").open(newline="") as source:
            pairs = [(int(x["global_frame"]), int(x["animal_id"])) for x in csv.DictReader(source)]
        expected = {(frame, animal) for frame in range(first, first+FRAMES) for animal in range(2)}
        if len(pairs) != 2*FRAMES or set(pairs) != expected:
            raise ValueError(f"Missing/duplicate frame-animal data: {task['id']}")
        quality = read(folder / "quality_v151r081.json")
        if len(quality["animals"]) != 2 or any(x["analyzed_frames"] != FRAMES for x in quality["animals"]):
            raise ValueError(f"Quality report has wrong denominator: {task['id']}")
        for animal in quality["animals"]:
            flattened = dict(task_id=task["id"], source_path=task["source_path"],
                             source_sha256=task["source_sha256"],
                             psc_model_version=MODEL, group_processor_version=PROCESSOR,
                             idtracker_estimated_accuracy=quality.get("idtracker_estimated_accuracy"),
                             idtracker_silhouette_score=quality.get("idtracker_silhouette_score"))
            flattened.update({key: value for key, value in animal.items() if key != "fungus_comparison"})
            for fungus, measures in animal["fungus_comparison"].items():
                flattened.update({f"{fungus}_{key}": value for key, value in measures.items()})
            quality_rows.append(flattened)
        rows.append(dict(task_id=task["id"], source_toml=task["source_path"],
                         first_global_frame=first, last_global_frame_inclusive=first+FRAMES-1,
                         analyzed_frame_count=FRAMES, encoded_video_frames=int(stream["nb_frames"]),
                         encoded_video_rate=stream["avg_frame_rate"],
                         psc_model_version=MODEL, group_processor_version=PROCESSOR,
                         review_view_version=VIEWER, pdf_track_style_version=PDF_STYLE,
                         analysis_manifest_sha256=sha(analysis / "manifest.json"),
                         viewer_video_sha256=sha(video), outlined_pdf_sha256=pdf["pdf_sha256"]))
    if len(rows) != 99 or len(quality_rows) != 198:
        raise ValueError(f"Expected 99 runs/198 animal quality rows, got {len(rows)}/{len(quality_rows)}")
    for filename, data in (("RUN_MANIFEST.csv", rows), ("BEETLE_QUALITY.csv", quality_rows)):
        with (root / filename).open("w", newline="") as stream:
            fields = list(dict.fromkeys(key for row in data for key in row))
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
    version = dict(schema="dyadic-2026-7200-frame-release-v1",
                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   eligible_trials=99, no_blob_exclusions=1, frames_per_trial=FRAMES,
                   source_toml_start_preserved=True, source_tracking_untouched=True,
                   psc_model_version=MODEL, group_processor_version=PROCESSOR,
                   review_view_version=VIEWER, pdf_track_style_version=PDF_STYLE,
                   review_status="UNREVIEWED", plan_sha256=sha(root / "plan.json"),
                   run_manifest_sha256=sha(root / "RUN_MANIFEST.csv"),
                   quality_csv_sha256=sha(root / "BEETLE_QUALITY.csv"),
                   code_snapshot=str(Path(__file__).resolve().parent),
                   output_manifest_code_sha256=sha(Path(__file__).with_name("output_manifest.py")),
                   processor_parity_report_sha256=sha(root / "PROCESSOR_PARITY.json"),
                   documentation_recovery_task_ids=[task["id"] for task in plan["tasks"]
                                                    if (root / "tasks" / task["id"] /
                                                        "status_v151r081_initial_failure.json").is_file()],
                   runner_sha256=sha(Path(__file__)))
    write(root / "VERSION_CONTROL.json", version)
    archive = root / "Dyadic_2026_99_7200frames_PSC_v1.5.1_processor0.8.1.zip"
    if archive.exists():
        raise FileExistsError(archive)
    with zipfile.ZipFile(archive, "w", allowZip64=True) as target:
        for name in ("README.md", "plan.json", "RUN_MANIFEST.csv", "BEETLE_QUALITY.csv",
                     "VERSION_CONTROL.json", "CODE_REPAIR.json", "PROCESSOR_PARITY.json"):
            if not (root / name).is_file():
                continue
            target.write(root / name, name)
        target.write(root / "code" / "dyadic_7200_release.py", "code/dyadic_7200_release.py")
        for task in plan["tasks"]:
            folder = root / "tasks" / task["id"]
            prefix = "tasks/" + task["id"] + "/"
            for name in ("source.toml", "submitted.toml"):
                target.write(folder / "input" / name, prefix + "input/" + name)
            for name in ("task.json", "final_status.json", "status_v151r081.json",
                         "status_v151r081_initial_failure.json", "analysis_v151r081.pipeline_receipt.json",
                         "quality_v151r081.json", "video_probe.json"):
                path = folder / name
                if path.is_file():
                    target.write(path, prefix + name)
            if task["excluded"]:
                for path in folder.glob("idtracker_attempt_*.log"):
                    target.write(path, prefix + path.name)
                continue
            for sub in ("analysis_v151r081", "review_compare_v151r081_v3", "pdf_outline_v1"):
                for path in sorted((folder / sub).iterdir()):
                    if path.is_file():
                        method = zipfile.ZIP_STORED if path.suffix in (".mp4", ".pdf", ".npz") else zipfile.ZIP_DEFLATED
                        target.write(path, prefix + sub + "/" + path.name, compress_type=method)
    with zipfile.ZipFile(archive) as source:
        bad = source.testzip()
        if bad is not None:
            raise ValueError(f"Corrupt ZIP member: {bad}")
    receipt = dict(version, archive=str(archive), archive_bytes=archive.stat().st_size,
                   archive_sha256=sha(archive), zip_integrity_passed=True)
    write(root / "RELEASE_RECEIPT.json", receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="mode", required=True)
    p = subs.add_parser("prepare")
    p.add_argument("source", type=Path)
    p.add_argument("destination", type=Path)
    p.add_argument("code_source", type=Path)
    r = subs.add_parser("run")
    r.add_argument("root", type=Path)
    r.add_argument("index", type=int)
    f = subs.add_parser("finalize")
    f.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.source, args.destination, args.code_source)
    elif args.mode == "run":
        sys.path.insert(0, str(args.root / "code"))
        run_one(args.root, args.index)
    else:
        sys.path.insert(0, str(args.root / "code"))
        finalize(args.root)


if __name__ == "__main__":
    main()
