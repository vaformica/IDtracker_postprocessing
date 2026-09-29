#!/usr/bin/env python3
"""Track corrected remaining 2024 GroupTrial TOMLs and analyze 9,000 frames.

The official 21-run release identifies which source TOMLs are still pending.
Five corrected, non-TEST six-beetle/four-ROI TOMLs are expected. Tracking runs
from immutable exact copies; source TOMLs and earlier releases are read-only.
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

SOURCE = Path("/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024")
OFFICIAL = Path("/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/grouptrial_2024_9000_frames_OFFICIAL_21_psc_v1_5_1_processor_0_8_1_20260928")
PYTHON = "/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python"
FFMPEG = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg"
FFPROBE = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe"
FRAMES = 9000
MODEL = "1.5.1"
PROCESSOR = "0.8.1-group"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, data: dict) -> None:
    temp = path.with_name(path.name + ".partial")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def video_info(path: Path) -> dict:
    raw = subprocess.check_output([FFPROBE, "-v", "error", "-select_streams", "v:0",
                                   "-show_entries", "stream=nb_frames,avg_frame_rate",
                                   "-of", "json", str(path)])
    return json.loads(raw)["streams"][0]


def stage(root: Path, code_source: Path) -> None:
    if root.exists():
        raise FileExistsError(root)
    with (OFFICIAL / "RUN_MANIFEST.csv").open(newline="") as stream:
        prior = list(csv.DictReader(stream))
    if len(prior) != 21:
        raise ValueError("Official 21-run baseline missing")
    completed = {Path(row["source_toml"]).name for row in prior}
    tasks, excluded = [], []
    for path in sorted(SOURCE.glob("*.toml")):
        if path.name in completed:
            continue
        record = dict(source_toml=str(path), source_sha256=sha(path))
        try:
            data = tomllib.loads(path.read_text())
            if "TEST" in path.stem.upper():
                raise ValueError("TEST/TESTSAVE configuration is not an official trial")
            if data.get("number_of_animals") != 6 or len(data.get("roi_list", [])) != 4:
                raise ValueError("Expected six animals, arena and three fungus ROIs")
            if data.get("use_bkg") is not True or data.get("check_segmentation") is True:
                raise ValueError("Background must be on and interactive segmentation off")
            area = data.get("area_ths")
            if not isinstance(area, list) or len(area) != 2 or not all(type(v) is float for v in area):
                raise ValueError("IDtracker requires floating-point area bounds")
            intervals, videos = data.get("tracking_intervals"), data.get("video_paths")
            if not isinstance(intervals, list) or len(intervals) != 1 or len(intervals[0]) != 2:
                raise ValueError("Missing or malformed tracking interval")
            if not isinstance(videos, list) or len(videos) != 1:
                raise ValueError("Expected one source video")
            start, end = intervals[0]
            video = Path(videos[0])
            if not video.is_file() or not 0 <= start < end or end - start < FRAMES:
                raise ValueError("Missing video or fewer than 9,000 source frames")
            info = video_info(video)
            if end > int(info["nb_frames"]):
                raise ValueError("TOML interval exceeds source video")
            record.update(index=len(tasks), label=path.stem, video=str(video),
                          first_global_frame=start, last_global_frame_inclusive=start+FRAMES-1,
                          toml_end_exclusive=end, video_frames=int(info["nb_frames"]),
                          fps=info["avg_frame_rate"])
            tasks.append(record)
        except Exception as exc:
            excluded.append(dict(record, reason=str(exc)))
    if len(tasks) != 5 or len(excluded) != 2:
        raise ValueError(f"Expected five newly corrected trials and two comparison/incomplete TOMLs: {len(tasks)} / {len(excluded)}")
    root.mkdir(parents=True)
    shutil.copytree(code_source, root / "code")
    (root / "tasks").mkdir()
    (root / "logs").mkdir()
    for item in tasks:
        out = root / "tasks" / item["label"]
        (out / "input").mkdir(parents=True)
        source = Path(item["source_toml"])
        shutil.copy2(source, out / "input" / "submitted.toml")
        if sha(out / "input" / "submitted.toml") != item["source_sha256"]:
            raise ValueError("Immutable TOML copy failed")
        item.update(submitted_toml=str(out / "input" / "submitted.toml"),
                    submitted_sha256=item["source_sha256"],
                    idtracker_output=str(out / "idtracker_output"))
        write(out / "submission_request.json", dict(
            source_toml=str(source), source_sha256=item["source_sha256"],
            submitted_toml=item["submitted_toml"],
            submitted_toml_sha256=item["submitted_sha256"],
            modified=False, tracking_interval=[item["first_global_frame"], item["toml_end_exclusive"]],
            analysis_interval_inclusive=[item["first_global_frame"], item["last_global_frame_inclusive"]]))
    write(root / "plan.json", dict(schema="grouptrial-remaining-9000-v1",
                                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                   baseline_official_21=str(OFFICIAL),
                                   baseline_manifest_sha256=sha(OFFICIAL / "RUN_MANIFEST.csv"),
                                   psc_model_version=MODEL, group_processor_version=PROCESSOR,
                                   frame_count=FRAMES, source_tomls_untouched=True,
                                   tasks=tasks, excluded=excluded))
    (root / "README.md").write_text(
        "# Corrected remaining 2024 GroupTrial TOMLs\n\n"
        "Five valid non-TEST six-beetle/four-ROI TOMLs have corrected starts. "
        "Each is tracked by IDtracker using an exact hashed TOML copy and then "
        "reanalyzed from its own start S through S+8,999 inclusive. PSC model "
        "1.5.1, processor 0.8.1-group, RAW/PSC viewer v3 and outlined-PSC PDFs "
        "match the official 21-trial release. The OLD_TEst comparison and "
        "TESTSAVE with zero ROIs and no interval are excluded. No original "
        "TOML or prior analysis is overwritten. Biological results remain UNREVIEWED.\n"
    )
    print(json.dumps({"tasks": len(tasks), "excluded": excluded, "root": str(root)}), flush=True)


def task(root: Path, index: int) -> tuple[dict, Path]:
    item = read(root / "plan.json")["tasks"][index]
    return item, root / "tasks" / item["label"]


def track(root: Path, index: int) -> None:
    item, out = task(root, index)
    if sha(Path(item["source_toml"])) != item["source_sha256"] or sha(Path(item["submitted_toml"])) != item["submitted_sha256"]:
        raise ValueError("Source/submitted TOML hash drift")
    if (out / "idtracker_output").exists():
        raise FileExistsError(out / "idtracker_output")
    command = [PYTHON, str(root / "code" / "firebird_idtracker_runner.py"),
               "--toml", item["submitted_toml"], "--output", item["idtracker_output"],
               "--workers", "16", "--device", "cuda", "--data-policy", "all"]
    with (out / "tracking_worker.log").open("x") as log:
        subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT, check=True)


def process(root: Path, index: int) -> None:
    item, out = task(root, index)
    status = out / "analysis_status.json"
    tracking_status = out / "status.json"
    tracking = read(tracking_status)
    if tracking.get("stage") not in ("COMPLETE_UNREVIEWED", "OUTPUT_READY_WITH_EXIT_WARNING"):
        raise ValueError("IDtracker trajectory is not verified complete")
    if not (out / "tracking_status.json").exists():
        shutil.copy2(tracking_status, out / "tracking_status.json")
    if status.exists():
        if read(status).get("stage") == "COMPLETE_UNREVIEWED":
            print("Already complete", item["label"])
            return
        raise FileExistsError(status)
    sys.path.insert(0, str(root / "code"))
    from grouptrial_2024_selected_postprocess import candidate
    selected = candidate(out)
    if selected is None:
        raise ValueError("No validated six-animal IDtracker trajectory")
    if selected["start"] != item["first_global_frame"] or selected["end_exclusive"] != item["toml_end_exclusive"]:
        raise ValueError("Tracked interval differs from submitted TOML")
    code = Path(__file__).resolve().parent
    command = [PYTHON, str(code / "run_group_pipeline.py"),
               "--session", selected["session"], "--trajectory", selected["trajectory"],
               "--source-toml", item["source_toml"], "--source-video", item["video"],
               "--analysis-output", str(out / "analysis"), "--review-output", str(out / "review"),
               "--start", str(item["first_global_frame"]),
               "--end", str(item["last_global_frame_inclusive"]),
               "--fps", str(selected["fps"]), "--label", item["label"],
               "--pdf-name", item["label"] + ".pdf",
               "--idtracker-python", PYTHON, "--ffmpeg", FFMPEG, "--ffprobe", FFPROBE]
    write(status, dict(stage="RUNNING", command=command, trajectory_sha256=selected["trajectory_sha256"]))
    try:
        with (out / "pipeline.log").open("x") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        from psc_release_validation import validate_bundle
        meta = read(out / "analysis" / "manifest.json")
        if (meta.get("persistent_model_version") != MODEL or meta.get("script_version") != PROCESSOR or
                int(meta["settings"]["start"]) != item["first_global_frame"] or
                int(meta["settings"]["window"]) != FRAMES - 1):
            raise ValueError("Wrong analysis version or frame window")
        validate_bundle(out / "analysis", MODEL, PROCESSOR)
        write(status, dict(stage="COMPLETE_UNREVIEWED", phase="numerical_and_source_review",
                           frame_count=FRAMES, trajectory_sha256=selected["trajectory_sha256"]))
        write(tracking_status, dict(stage="COMPLETE_UNREVIEWED", phase="numerical_and_source_review",
                                    tracking_status_preserved=str(out / "tracking_status.json"),
                                    frame_count=FRAMES))
        from rebuild_raw_psc_compare_reviews import rebuild_task
        rebuild_task(root, "grouptrial", item, FFMPEG)
        from render_psc_outlined_pdf import render
        render(out / "analysis", out / "pdf_outline_v1")
        video = out / "review_compare_v3" / "review_video.mp4"
        info = video_info(video)
        if int(info["nb_frames"]) != FRAMES:
            raise ValueError("Comparison review video does not have 9,000 frames")
        with (out / "analysis" / "frame_data.csv").open(newline="") as stream:
            pairs = [(int(row["global_frame"]), int(row["animal_id"])) for row in csv.DictReader(stream)]
        expected = {(frame, animal) for frame in range(item["first_global_frame"], item["first_global_frame"]+FRAMES) for animal in range(6)}
        if len(pairs) != FRAMES*6 or set(pairs) != expected:
            raise ValueError("Missing/duplicate frame-animal rows")
        write(out / "video_probe.json", info)
        write(status, dict(stage="COMPLETE_UNREVIEWED", frame_count=FRAMES,
                           trajectory_sha256=selected["trajectory_sha256"],
                           viewer_video_sha256=sha(video),
                           completed_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        write(tracking_status, dict(stage="COMPLETE_UNREVIEWED", frame_count=FRAMES,
                                    tracking_status_preserved=str(out / "tracking_status.json"),
                                    trajectory_sha256=selected["trajectory_sha256"],
                                    viewer_video_sha256=sha(video)))
    except BaseException as error:
        write(status, dict(stage="FAILED", error=repr(error)))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("stage")
    p.add_argument("root", type=Path)
    p.add_argument("code_source", type=Path)
    for mode in ("track", "process"):
        p = sub.add_parser(mode)
        p.add_argument("root", type=Path)
        p.add_argument("index", type=int)
    args = parser.parse_args()
    if args.mode == "stage":
        stage(args.root, args.code_source)
    elif args.mode == "track":
        track(args.root, args.index)
    else:
        process(args.root, args.index)


if __name__ == "__main__":
    main()
