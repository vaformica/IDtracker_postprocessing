#!/usr/bin/env python3
"""Run the complete six-beetle analysis and portable video-review pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from build_canonical_review import build as build_review
from processor import load_rois as load_session_rois


BASE = Path(__file__).resolve().parent
TRAJECTORY_NAMES = (
    "validated.npy",
    "without_gaps.npy",
    "trajectories_wo_gaps.npy",
    "trajectories_without_gaps.npy",
    "trajectories.npy",
    "trajectories.h5",
    "trajectories.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_trajectory(session: Path) -> Path:
    candidates = []
    for name in TRAJECTORY_NAMES:
        direct = [session / name, session / "trajectories" / name]
        found = [path for path in direct if path.is_file()]
        if not found:
            found = list(session.rglob(name))
        if found:
            candidates = sorted(set(found))
            break
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one preferred trajectory under {session}; found {len(candidates)}: {candidates}")
    return candidates[0]


def session_json(session: Path) -> Path:
    direct = session / "session.json"
    matches = [direct] if direct.is_file() else list(session.rglob("session.json"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one session.json under {session}; found {len(matches)}")
    return matches[0]


def load_rois(session: Path):
    polygons = load_session_rois(session)
    if len(polygons) != 4:
        raise ValueError("Six-beetle processing requires exactly four ROIs: arena then fungus 1, 2, 3")
    if any(polygon.ndim != 2 or polygon.shape[1] != 2 for polygon in polygons):
        raise ValueError("Every ROI must be an x/y polygon")
    return polygons


def probe_video(video: Path, ffprobe: str) -> tuple[int, int]:
    command = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(video),
    ]
    payload = json.loads(subprocess.run(command, check=True, capture_output=True, text=True).stdout)
    stream = payload["streams"][0]
    return int(stream["width"]), int(stream["height"])


def arena_crop(rois, video_width: int, video_height: int, padding: int = 20) -> tuple[int, int, int, int]:
    arena = np.asarray(rois[0], dtype=float)
    x0 = max(0, int(np.floor(arena[:, 0].min())) - padding)
    y0 = max(0, int(np.floor(arena[:, 1].min())) - padding)
    x1 = min(video_width, int(np.ceil(arena[:, 0].max())) + padding)
    y1 = min(video_height, int(np.ceil(arena[:, 1].max())) + padding)
    # H.264/yuv420 requires even crop dimensions and offsets.
    x0 -= x0 % 2
    y0 -= y0 % 2
    x1 -= (x1 - x0) % 2
    y1 -= (y1 - y0) % 2
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Arena ROI does not define a valid video crop")
    return x0, y0, x1 - x0, y1 - y0


def ensure_blob_evidence(session: Path, idtracker_python: str, generated_output: Path | None = None) -> Path:
    evidence = session / "blob_evidence.json"
    source = session / "preprocessing" / "list_of_blobs.pickle"
    if evidence.is_file():
        payload = json.loads(evidence.read_text())
        if payload.get("schema") != "idtracker-blob-evidence-v1" or not payload.get("source_sha256"):
            raise RuntimeError("Existing blob_evidence.json lacks the required schema or source hash")
        if source.is_file() and payload.get("source_sha256") != sha256(source):
            raise RuntimeError("Existing blob_evidence.json does not match list_of_blobs.pickle; refusing stale evidence")
        return evidence
    if not source.is_file():
        raise FileNotFoundError("Persistent pile analysis requires preprocessing/list_of_blobs.pickle or a hashed blob_evidence.json export")
    evidence = generated_output or evidence
    evidence.parent.mkdir(parents=True, exist_ok=True)
    if evidence.exists():
        raise FileExistsError(f"Refusing existing generated evidence: {evidence}")
    subprocess.run(
        [idtracker_python, str(BASE / "export_blob_evidence.py"), str(session), "--output", str(evidence)],
        check=True,
    )
    if not evidence.is_file():
        raise RuntimeError("Blob exporter completed without creating blob_evidence.json")
    return evidence


def make_review_video(
    source: Path,
    destination: Path,
    start: int,
    end: int,
    crop: tuple[int, int, int, int],
    ffmpeg: str,
):
    x, y, width, height = crop
    filter_graph = (
        f"trim=start_frame={start}:end_frame={end + 1},setpts=PTS-STARTPTS,"
        f"crop={width}:{height}:{x}:{y},scale=1280:920:flags=lanczos"
    )
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-vf",
            filter_graph,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(destination),
        ],
        check=True,
    )


def run(args) -> Path:
    session = Path(args.session).resolve()
    source_video = Path(args.source_video).resolve()
    analysis_output = Path(args.analysis_output).resolve()
    review_output = Path(args.review_output).resolve()
    if analysis_output.exists() or review_output.exists():
        raise FileExistsError("Analysis and review outputs must both be new directories")
    if not session.is_dir() or not source_video.is_file():
        raise FileNotFoundError("Session directory and source video must exist")
    if args.end < args.start:
        raise ValueError("end must be greater than or equal to start")
    if args.fps <= 0 or not np.isfinite(args.fps):
        raise ValueError("fps must be finite and positive")

    trajectory = Path(args.trajectory).resolve() if args.trajectory else find_trajectory(session)
    rois = load_rois(session)
    analysis_output.parent.mkdir(parents=True, exist_ok=True)
    review_output.parent.mkdir(parents=True, exist_ok=True)
    generated_evidence = analysis_output.parent / f"{analysis_output.name}.blob_evidence.json"
    evidence = ensure_blob_evidence(session, args.idtracker_python, generated_evidence)
    window = args.end - args.start
    pdf_name = args.pdf_name or f"{args.label}.pdf"
    command = [
        sys.executable,
        str(BASE / "six_beetle_processor.py"),
        "--trajectory",
        str(trajectory),
        "--session",
        str(session),
        "--blob-evidence",
        str(evidence),
        "--output",
        str(analysis_output),
        "--start",
        str(args.start),
        "--window",
        str(window),
        "--video",
        source_video.name,
        "--cell-label",
        args.label,
        "--pdf-name",
        pdf_name,
        "--fps",
        str(args.fps),
        "--threshold",
        str(args.movement_threshold_px),
        "--wall-buffer-px",
        str(args.wall_buffer_px),
        "--fungus-buffer-px",
        str(args.fungus_buffer_px),
        "--social-distance-threshold-px",
        str(args.proximity_px),
        "--jump-threshold-px",
        str(args.jump_threshold_px),
        "--reconstruction-speed-px",
        str(args.reconstruction_speed_px),
    ]
    subprocess.run(command, check=True)

    if args.prepared_review_video and not args.crop:
        raise ValueError("--prepared-review-video requires --crop in original-video coordinates")
    if args.crop:
        crop = tuple(args.crop)
    else:
        video_width, video_height = probe_video(source_video, args.ffprobe)
        crop = arena_crop(rois, video_width, video_height, args.crop_padding)
    temporary = Path(tempfile.mkdtemp(prefix=".six-beetle-video-", dir=review_output.parent))
    try:
        cropped_video = temporary / "review_video.mp4"
        if args.prepared_review_video:
            prepared = Path(args.prepared_review_video).resolve()
            if not prepared.is_file():
                raise FileNotFoundError(prepared)
            try:
                os.link(prepared, cropped_video)
            except OSError:
                shutil.copy2(prepared, cropped_video)
        else:
            make_review_video(source_video, cropped_video, args.start, args.end, crop, args.ffmpeg)
        html = build_review(
            analysis_output,
            cropped_video,
            review_output,
            crop,
            args.fps,
            label=args.label,
        )
    finally:
        shutil.rmtree(temporary, ignore_errors=True)

    manifest = json.loads((analysis_output / "manifest.json").read_text())
    receipt = dict(
        schema="six-beetle-pipeline-run-v1",
        created_utc=datetime.now(timezone.utc).isoformat(),
        status="COMPLETE_UNREVIEWED",
        model=f"persistent-groups-{manifest.get('persistent_model_version')}",
        processor_version=manifest.get("script_version"),
        session=str(session),
        trajectory=str(trajectory),
        trajectory_sha256=sha256(trajectory),
        blob_evidence=str(evidence),
        blob_evidence_sha256=sha256(evidence),
        source_video=str(source_video),
        source_video_sha256=sha256(source_video),
        prepared_review_video=str(Path(args.prepared_review_video).resolve()) if args.prepared_review_video else None,
        analysis_output=str(analysis_output),
        review_output=str(review_output),
        review_html=str(html),
        settings=dict(
            start=args.start,
            end_inclusive=args.end,
            fps=args.fps,
            movement_threshold_px=args.movement_threshold_px,
            wall_buffer_px=args.wall_buffer_px,
            fungus_buffer_px=args.fungus_buffer_px,
            proximity_px=args.proximity_px,
            jump_threshold_px=args.jump_threshold_px,
            reconstruction_speed_px=args.reconstruction_speed_px,
            crop=list(crop),
        ),
        command=command,
    )
    receipt_path = analysis_output.parent / f"{analysis_output.name}.pipeline_receipt.json"
    if receipt_path.exists():
        raise FileExistsError(receipt_path)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt_path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--session", required=True)
    result.add_argument("--trajectory")
    result.add_argument("--source-video", required=True)
    result.add_argument("--prepared-review-video", help="Already clipped/cropped MP4 for local rebuilding; requires --crop")
    result.add_argument("--analysis-output", required=True)
    result.add_argument("--review-output", required=True)
    result.add_argument("--start", type=int, required=True)
    result.add_argument("--end", type=int, required=True, help="Inclusive global frame")
    result.add_argument("--fps", type=float, required=True)
    result.add_argument("--label", required=True)
    result.add_argument("--pdf-name")
    result.add_argument("--movement-threshold-px", type=float, default=30.0)
    result.add_argument("--wall-buffer-px", type=float, default=30.0)
    result.add_argument("--fungus-buffer-px", type=float, default=30.0)
    result.add_argument("--proximity-px", type=float, default=60.0)
    result.add_argument("--jump-threshold-px", type=float, default=200.0)
    result.add_argument("--reconstruction-speed-px", type=float, default=100.0)
    result.add_argument("--crop", type=int, nargs=4, metavar=("X", "Y", "WIDTH", "HEIGHT"))
    result.add_argument("--crop-padding", type=int, default=20)
    result.add_argument(
        "--idtracker-python",
        default="/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python",
    )
    result.add_argument(
        "--ffmpeg",
        default="/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg",
    )
    result.add_argument(
        "--ffprobe",
        default="/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe",
    )
    return result


def main():
    receipt = run(parser().parse_args())
    print(f"Wrote complete UNREVIEWED pipeline receipt: {receipt}")


if __name__ == "__main__":
    main()
