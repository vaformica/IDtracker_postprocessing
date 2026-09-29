#!/usr/bin/env python3
"""Build a 21-trial official 9,000-frame release with non-TEST Box01 OLD."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


MODEL = "1.5.1"
PROCESSOR = "0.8.1-group"
FRAMES = 9000
TEST = "groupagetrial01_062024_Box01_OLD_TEst"
OFFICIAL = "groupagetrial01_062024_Box01_OLD"
FFPROBE = "/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def check_row(label: str, task: Path, source_toml: Path, submitted_toml: Path) -> dict:
    analysis = task / "analysis"
    review = task / "review_compare_v3"
    outline = task / "pdf_outline_v1"
    status = read(task / "status.json")
    meta = read(analysis / "manifest.json")
    view = read(review / "source_manifest.json")
    pdf = read(outline / "render_manifest.json")
    video = review / "review_video.mp4"
    first = int(meta["settings"]["start"])
    if (status.get("stage") != "COMPLETE_UNREVIEWED" or "phase" in status or
        meta.get("persistent_model_version") != MODEL or meta.get("script_version") != PROCESSOR or
        meta.get("qc_status") != "UNREVIEWED" or int(meta["settings"]["window"]) != FRAMES - 1 or
        view.get("review_view_version") != "raw-psc-compare-v3" or
        view.get("analysis_manifest_sha256") != sha(analysis / "manifest.json") or
        view.get("analysis_frame_count") != FRAMES or
        view.get("copied_video_sha256") != sha(video) or
        pdf.get("psc_model_version") != MODEL or pdf.get("processor_version") != PROCESSOR or
        pdf.get("pdf_track_style_version") != "outlined-psc-v1" or
        pdf.get("source_manifest_sha256") != sha(analysis / "manifest.json") or
        pdf.get("pdf_sha256") != sha(outline / pdf["pdf_filename"])):
        raise ValueError(f"Failed version/hash gate: {label}")
    stream = json.loads(subprocess.check_output([
        FFPROBE, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=nb_frames,r_frame_rate,avg_frame_rate",
        "-of", "json", str(video)]))["streams"][0]
    if int(stream["nb_frames"]) != FRAMES or stream["avg_frame_rate"] != "30/1":
        raise ValueError(f"Failed encoded-video frame gate: {label}: {stream}")
    with (analysis / "frame_data.csv").open(newline="") as source:
        observed = [(int(x["global_frame"]), int(x["animal_id"])) for x in csv.DictReader(source)]
    expected = {(frame, animal) for frame in range(first, first + FRAMES) for animal in range(6)}
    if len(observed) != 6 * FRAMES or set(observed) != expected:
        raise ValueError(f"Missing or duplicated frame/animal rows: {label}")
    if not source_toml.is_file() or not submitted_toml.is_file():
        raise FileNotFoundError(f"Missing source/submitted TOML: {label}")
    return dict(label=label, source_toml=str(source_toml), submitted_toml=str(submitted_toml),
                source_toml_sha256=sha(source_toml), submitted_toml_sha256=sha(submitted_toml),
                first_global_frame=first, last_global_frame_inclusive=first + FRAMES - 1,
                analyzed_frame_count=FRAMES, encoded_video_frames=FRAMES,
                encoded_video_frame_rate=stream["avg_frame_rate"],
                psc_model_version=MODEL, group_processor_version=PROCESSOR,
                reviewer_status="UNREVIEWED", analysis_manifest_sha256=sha(analysis / "manifest.json"),
                video_sha256=sha(video), outlined_pdf_sha256=pdf["pdf_sha256"],
                task_folder=str(task))


def build(provisional: Path, official_box01: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    plan = read(provisional / "plan.json")
    rows = []
    for item in plan["tasks"]:
        label = item["label"]
        if label == TEST:
            continue
        folder = provisional / "tasks" / label
        rows.append(check_row(label, folder, Path(item["source_toml"]), Path(item["submitted_toml"])))
    receipt = read(official_box01 / "RELEASE_RECEIPT.json")
    if receipt.get("label") != OFFICIAL or receipt.get("analyzed_frame_count") != FRAMES:
        raise ValueError("Official Box01 OLD release is missing or invalid")
    box = official_box01 / "tasks" / OFFICIAL
    rows.append(check_row(OFFICIAL, box, Path(receipt["source_toml"]), official_box01 / "input" / "submitted.toml"))
    if len(rows) != 21 or len({r["label"] for r in rows}) != 21 or any(r["label"] == TEST for r in rows):
        raise ValueError("Official collection must contain 21 unique non-TEST trials")
    rows.sort(key=lambda row: row["label"])
    destination.mkdir(parents=True)
    (destination / "runs").mkdir()
    for row in rows:
        (destination / "runs" / row["label"]).symlink_to(row["task_folder"], target_is_directory=True)
    readme = (
        "# Official 2024 GroupTrial six-beetle release: first 9,000 tracked frames\n\n"
        "Twenty-one official trials are included. Each analysis starts at its own "
        "source TOML tracking start S and includes global frames S through S+8,999 "
        "inclusive. The windows are not all frame 0–8,999. Source video and encoded "
        "review video rates are 30 fps, so each trial covers 5 minutes; across 21 "
        "videos this is 105 minutes (1 hour 45 minutes) of reviewed video, not 2.5 hours.\n\n"
        "GroupTrial 01 Box01 OLD uses the NON-TEST source TOML. Its source video path "
        "was nonexistent, so only that path was repaired in an immutable submitted "
        "copy. The original thresholds, ROIs, background subtraction, and tracking "
        "interval were retained. Box01 OLD_TEst is comparison-only and is excluded "
        "from this official collection. The six other top-level TOMLs that lack "
        "required inputs remain excluded; see the prior TOML audit.\n\n"
        "All trials use PSC model 1.5.1, group processor 0.8.1-group, RAW/PSC "
        "viewer v3, and outlined-PSC PDFs. Results are computational and "
        "UNREVIEWED for biological interpretation. Source TOMLs, IDtracker "
        "tracking, and earlier longer analyses are unchanged.\n\n"
        "runs/ contains symlinks to the versioned source task folders, so it adds "
        "almost no storage. Download the complete ZIP for a portable copy. "
        "RUN_MANIFEST.csv gives start/end frames and file hashes for every trial.\n"
    )
    (destination / "README.md").write_text(readme)
    with (destination / "RUN_MANIFEST.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    version = dict(schema="grouptrial-2024-9000-official-collection-v1",
                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   official_trials=21, comparison_only_toml=TEST,
                   official_box01_toml=OFFICIAL,
                   frames_per_trial=FRAMES, source_start_preserved=True,
                   source_tomls_untouched=True, tracking_untouched=True,
                   psc_model_version=MODEL, group_processor_version=PROCESSOR,
                   review_view_version="raw-psc-compare-v3", pdf_track_style_version="outlined-psc-v1",
                   qc_status="UNREVIEWED", run_manifest_sha256=sha(destination / "RUN_MANIFEST.csv"),
                   collection_code_sha256=sha(Path(__file__)),
                   provisional_release=str(provisional), official_box01_release=str(official_box01))
    (destination / "VERSION_CONTROL.json").write_text(json.dumps(version, indent=2) + "\n")
    archive = destination / "GroupTrial_2024_OFFICIAL_21_9000frames_PSC_v1.5.1_processor0.8.1.zip"
    with zipfile.ZipFile(archive, "w", allowZip64=True) as target:
        for name in ("README.md", "RUN_MANIFEST.csv", "VERSION_CONTROL.json"):
            target.write(destination / name, name)
        target.write(Path(__file__), "code/grouptrial_9000_official_collection.py")
        for row in rows:
            label = row["label"]
            task = Path(row["task_folder"])
            target.write(row["source_toml"], f"{label}/source.toml")
            target.write(row["submitted_toml"], f"{label}/submitted.toml")
            for sub in ("analysis", "review_compare_v3", "pdf_outline_v1"):
                for path in sorted((task / sub).iterdir()):
                    if path.is_file():
                        method = zipfile.ZIP_STORED if path.suffix in (".mp4", ".pdf", ".npz") else zipfile.ZIP_DEFLATED
                        target.write(path, f"{label}/{sub}/{path.name}", compress_type=method)
            for name in ("status.json", "video_probe.json", "analysis.pipeline_receipt.json"):
                path = task / name
                if path.is_file():
                    target.write(path, f"{label}/{name}")
    with zipfile.ZipFile(archive) as target:
        if target.testzip() is not None:
            raise ValueError("Official ZIP failed integrity test")
    receipt = dict(version, archive=str(archive), archive_bytes=archive.stat().st_size,
                   archive_sha256=sha(archive), zip_test_passed=True)
    (destination / "RELEASE_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: grouptrial_9000_official_collection.py PROVISIONAL_ROOT OFFICIAL_BOX01_ROOT DESTINATION")
    build(*(Path(arg) for arg in sys.argv[1:]))
