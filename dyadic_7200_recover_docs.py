#!/usr/bin/env python3
"""Finish a 7,200-frame dyadic pilot after an output-guide-only failure.

The numerical analysis, source review, and IDtracker tracking are read-only.
This only writes the missing output guide, tracking-quality JSON, viewer v3,
outlined PDF, and recovery receipts in the new versioned release directory.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import shutil
import sys

from dyadic_7200_release import FFMPEG, FRAMES, MODEL, PROCESSOR, read, sha, write, probe


def recover(root: Path, index: int) -> None:
    task = read(root / "plan.json")["tasks"][index]
    if task["excluded"]:
        raise ValueError("Excluded task cannot be recovered")
    folder = root / "tasks" / task["id"]
    analysis = folder / "analysis_v151r081"
    review = folder / "review_v151r081"
    quality = folder / "quality_v151r081.json"
    status = folder / "status_v151r081.json"
    if read(status).get("stage") != "FAILED":
        raise ValueError("Expected documented output-guide failure")
    if (analysis / "OUTPUT_MANIFEST.md").exists() or quality.exists() or (folder / "review_compare_v151r081_v3").exists():
        raise FileExistsError("Recovery already started; inspect outputs")
    old_log = (folder / "pipeline.log").read_text(errors="replace")
    if "Update output-manifest JSON definitions" not in old_log or "pdf_track_style_version" not in old_log:
        raise ValueError("This is not the known documentation-only failure")
    shutil.copy2(status, folder / "status_v151r081_initial_failure.json")
    from psc_release_validation import validate_bundle
    meta = read(analysis / "manifest.json")
    if (meta.get("persistent_model_version") != MODEL or meta.get("script_version") != PROCESSOR or
            int(meta["settings"]["start"]) != task["first_global_frame"] or
            int(meta["settings"]["window"]) != FRAMES-1):
        raise ValueError("Published numerical window/version mismatch")
    validate_bundle(analysis, MODEL, PROCESSOR)
    source = read(review / "source_manifest.json")
    video = review / source["video"]
    if (source.get("analysis_manifest_sha256") != sha(analysis / "manifest.json") or
            source.get("copied_video_sha256") != sha(video) or
            int(probe(video)["nb_frames"]) != FRAMES):
        raise ValueError("Published source review does not match numerical analysis")
    receipt = folder / "analysis_v151r081.pipeline_receipt.json"
    write(receipt, dict(schema="dyadic-7200-documentation-recovery-v1",
                        created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                        reason="Prior code snapshot lacked pdf_track_style_version output-guide definition",
                        numerical_analysis_untouched=True, source_review_untouched=True,
                        analysis_manifest_sha256=sha(analysis / "manifest.json"),
                        source_review_manifest_sha256=sha(review / "source_manifest.json"),
                        source_review_video_sha256=sha(video),
                        failure_status_sha256=sha(folder / "status_v151r081_initial_failure.json")))
    from output_manifest import write_output_manifest
    write_output_manifest(analysis, review, receipt=receipt,
                          source_toml=Path(task["source_path"]))
    from dyadic_quality import summary
    quality.write_text(json.dumps(summary(analysis, Path(task["session"]),
                                          task["source_path"], task["source_sha256"]),
                                  indent=2, allow_nan=False) + "\n")
    write(status, dict(stage="COMPLETE_UNREVIEWED", phase="numerical_and_source_review",
                       interval_inclusive=[task["first_global_frame"], task["last_global_frame_inclusive"]],
                       frame_count=FRAMES, documentation_recovery=str(receipt)))
    from rebuild_raw_psc_compare_reviews import rebuild_task
    rebuild_task(root, "dyadic", task, FFMPEG)
    from render_psc_outlined_pdf import render
    render(analysis, folder / "pdf_outline_v1")
    viewer = folder / "review_compare_v151r081_v3" / "review_video.mp4"
    stream = probe(viewer)
    if int(stream["nb_frames"]) != FRAMES:
        raise ValueError("Recovered viewer is not 7,200 frames")
    write(folder / "video_probe.json", stream)
    write(status, dict(stage="COMPLETE_UNREVIEWED",
                       utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                       interval_inclusive=[task["first_global_frame"], task["last_global_frame_inclusive"]],
                       frame_count=FRAMES, analysis=str(analysis),
                       review=str(folder / "review_compare_v151r081_v3"),
                       outlined_pdf=str(folder / "pdf_outline_v1"), quality=str(quality),
                       documentation_recovery=str(receipt)))
    print(json.dumps({"recovered": task["id"], "video_sha256": sha(viewer),
                      "analysis_manifest_sha256": sha(analysis / "manifest.json")}), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: dyadic_7200_recover_docs.py ROOT INDEX")
    recover(Path(sys.argv[1]), int(sys.argv[2]))
