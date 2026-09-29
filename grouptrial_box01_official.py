#!/usr/bin/env python3
"""Finish the official non-TEST GroupTrial 01 Box01 OLD tracking run.

The source TOML is immutable. The submitted copy repairs only its video path;
the original interval is tracked, and the first 9,000 requested observations
are reanalyzed under PSC 1.5.1 / processor 0.8.1-group.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
import zipfile

import numpy as np


PYTHON = "/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python"
FFMPEG = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg"
FFPROBE = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe"
MODEL = "1.5.1"
PROCESSOR = "0.8.1-group"
LABEL = "groupagetrial01_062024_Box01_OLD"
FIRST = 250
COUNT = 9000
LAST = FIRST + COUNT - 1


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, value: dict) -> None:
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def tracking_session(root: Path) -> tuple[Path, Path]:
    receipt = read_json(root / "submission_request.json")
    source = Path(receipt["source_toml"])
    submitted = Path(receipt["submitted_toml"])
    if sha(source) != receipt["source_sha256"] or sha(submitted) != receipt["submitted_sha256"]:
        raise ValueError("Source or submitted TOML hash changed")
    original = tomllib.loads(source.read_text())
    corrected = tomllib.loads(submitted.read_text())
    if any(original[key] != corrected[key] for key in original if key != "video_paths"):
        raise ValueError("Submitted TOML changed more than the video path")
    if corrected["number_of_animals"] != 6 or len(corrected["roi_list"]) != 4 or not corrected["use_bkg"]:
        raise ValueError("Unexpected animal, ROI, or background setting")
    if corrected["tracking_intervals"] != [[FIRST, 16998]]:
        raise ValueError("Unexpected source tracking interval")
    sessions = [p.parent for p in (root / "idtracker_output").rglob("session.json")
                if (p.parent / "trajectories" / "trajectories.npy").is_file()]
    if len(sessions) != 1:
        raise ValueError(f"Expected one complete IDtracker session, got {len(sessions)}")
    session = sessions[0]
    trajectory = session / "trajectories" / "trajectories.npy"
    data = np.load(trajectory, allow_pickle=True)
    if data.shape == ():
        data = data.item()["trajectories"]
    if data.ndim != 3 or data.shape[1:] != (6, 2) or len(data) < 16998:
        raise ValueError(f"Incomplete six-animal trajectory: {data.shape}")
    metadata = read_json(session / "session.json")
    if (metadata.get("number_of_animals") != 6 or
        metadata.get("tracking_intervals") != [[FIRST, 16998]] or
        metadata.get("use_bkg") is not True):
        raise ValueError("IDtracker session settings differ from submitted TOML")
    return session, trajectory


def process(root: Path) -> None:
    session, trajectory = tracking_session(root)
    task = root / "tasks" / LABEL
    task.mkdir(parents=True, exist_ok=True)
    status = task / "status.json"
    if status.exists():
        raise FileExistsError(status)
    submitted = tomllib.loads((root / "input" / "submitted.toml").read_text())
    source_video = Path(submitted["video_paths"][0])
    code = root / "code"
    command = [PYTHON, str(code / "run_group_pipeline.py"),
               "--session", str(session), "--trajectory", str(trajectory),
               "--source-toml", str(Path(read_json(root / "submission_request.json")["source_toml"])),
               "--source-video", str(source_video),
               "--analysis-output", str(task / "analysis"),
               "--review-output", str(task / "review"),
               "--start", str(FIRST), "--end", str(LAST), "--fps", "30",
               "--label", LABEL, "--pdf-name", LABEL + ".pdf",
               "--idtracker-python", PYTHON, "--ffmpeg", FFMPEG, "--ffprobe", FFPROBE]
    write_json(status, dict(stage="RUNNING", command=command,
                            trajectory_sha256=sha(trajectory),
                            started_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    try:
        with (task / "pipeline.log").open("x") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        meta = read_json(task / "analysis" / "manifest.json")
        if (meta.get("persistent_model_version") != MODEL or meta.get("script_version") != PROCESSOR or
            meta.get("qc_status") != "UNREVIEWED" or
            int(meta["settings"]["start"]) != FIRST or int(meta["settings"]["window"]) != COUNT - 1):
            raise ValueError("PSC, processor, QC, or frame window mismatch")
        from psc_release_validation import validate_bundle
        validate_bundle(task / "analysis", MODEL, PROCESSOR)
        write_json(status, dict(stage="COMPLETE_UNREVIEWED", phase="numerical_and_source_review",
                                start=FIRST, end_inclusive=LAST, frame_count=COUNT))
        from rebuild_raw_psc_compare_reviews import rebuild_task
        rebuild_task(root, "grouptrial", {"source_toml": read_json(root / "submission_request.json")["source_toml"],
                                          "video": str(source_video)}, FFMPEG)
        from render_psc_outlined_pdf import render
        render(task / "analysis", task / "pdf_outline_v1")
        video = task / "review_compare_v3" / "review_video.mp4"
        probe = json.loads(subprocess.check_output([
            FFPROBE, "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=nb_frames,r_frame_rate,avg_frame_rate", "-of", "json", str(video)]))["streams"][0]
        if int(probe["nb_frames"]) != COUNT or probe["avg_frame_rate"] != "30/1":
            raise ValueError(f"Review video count or fps mismatch: {probe}")
        with (task / "analysis" / "frame_data.csv").open(newline="") as stream:
            frames = {int(row["global_frame"]) for row in csv.DictReader(stream)}
        if frames != set(range(FIRST, LAST + 1)):
            raise ValueError("Frame-level CSV interval mismatch")
        write_json(task / "video_probe.json", probe)
        write_json(status, dict(stage="COMPLETE_UNREVIEWED", start=FIRST,
                                end_inclusive=LAST, frame_count=COUNT,
                                trajectory_sha256=sha(trajectory),
                                video_sha256=sha(video),
                                completed_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    except Exception as exc:
        write_json(status, dict(stage="FAILED", error=repr(exc)))
        raise


def package(root: Path) -> None:
    task = root / "tasks" / LABEL
    status = read_json(task / "status.json")
    analysis = task / "analysis"
    meta = read_json(analysis / "manifest.json")
    review = task / "review_compare_v3"
    review_meta = read_json(review / "source_manifest.json")
    outline = task / "pdf_outline_v1"
    outline_meta = read_json(outline / "render_manifest.json")
    if (status.get("stage") != "COMPLETE_UNREVIEWED" or
        status.get("frame_count") != COUNT or
        meta.get("persistent_model_version") != MODEL or
        meta.get("script_version") != PROCESSOR or
        review_meta.get("review_view_version") != "raw-psc-compare-v3" or
        review_meta.get("analysis_manifest_sha256") != sha(analysis / "manifest.json") or
        review_meta.get("analysis_frame_count") != COUNT or
        outline_meta.get("pdf_track_style_version") != "outlined-psc-v1" or
        outline_meta.get("source_manifest_sha256") != sha(analysis / "manifest.json")):
        raise ValueError("Official bundle failed version or provenance gate")
    archive = root / "GroupTrial01_Box01_OLD_OFFICIAL_9000_frames_PSC_v1.5.1_processor0.8.1.zip"
    if archive.exists():
        raise FileExistsError(archive)
    receipt = dict(schema="grouptrial-box01-old-official-v1", label=LABEL,
                   source_toml=read_json(root / "submission_request.json")["source_toml"],
                   submitted_toml_sha256=read_json(root / "submission_request.json")["submitted_sha256"],
                   psc_model_version=MODEL, group_processor_version=PROCESSOR,
                   review_view_version="raw-psc-compare-v3", pdf_style_version="outlined-psc-v1",
                   first_global_frame=FIRST, last_global_frame_inclusive=LAST,
                   analyzed_frame_count=COUNT, review_status="UNREVIEWED",
                   source_toml_untouched=True, tracking_session=str(tracking_session(root)[0]))
    write_json(root / "VERSION_CONTROL.json", receipt)
    with zipfile.ZipFile(archive, "w", allowZip64=True) as z:
        for source in (root / "README.md", root / "submission_request.json", root / "VERSION_CONTROL.json",
                       root / "input" / "submitted.toml", Path(receipt["source_toml"])):
            z.write(source, source.name if source.suffix != ".toml" else ("submitted.toml" if source.parent.name == "input" else "source.toml"))
        for sub in ("analysis", "review_compare_v3", "pdf_outline_v1"):
            for source in sorted((task / sub).iterdir()):
                if source.is_file():
                    method = zipfile.ZIP_STORED if source.suffix in (".mp4", ".pdf", ".npz") else zipfile.ZIP_DEFLATED
                    z.write(source, f"{LABEL}/{sub}/{source.name}", compress_type=method)
        for name in ("status.json", "video_probe.json"):
            z.write(task / name, f"{LABEL}/{name}")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("Official ZIP failed integrity check")
    receipt.update(archive=str(archive), archive_sha256=sha(archive), archive_bytes=archive.stat().st_size)
    write_json(root / "RELEASE_RECEIPT.json", receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in ("process", "package"):
        raise SystemExit("usage: grouptrial_box01_official.py process|package ROOT")
    root = Path(sys.argv[2])
    sys.path.insert(0, str(root / "code"))
    (process if sys.argv[1] == "process" else package)(root)


if __name__ == "__main__":
    main()
