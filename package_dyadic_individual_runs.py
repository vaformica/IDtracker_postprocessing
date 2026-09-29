from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

root = Path("/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_fight_7200_frames_psc_v1_5_1_processor_0_8_1_20260928")
source = root / "Dyadic_2026_99_7200frames_PSC_v1.5.1_processor0.8.1.zip"
output = root / "individual_run_zips"
output.mkdir(exist_ok=True)

with (root / "RUN_MANIFEST.csv").open(newline="") as handle:
    runs = list(csv.DictReader(handle))
with (root / "BEETLE_QUALITY.csv").open(newline="") as handle:
    quality = list(csv.DictReader(handle))
assert len(runs) == 99 and len(quality) == 198
assert len({r["task_id"] for r in runs}) == 99

def csv_bytes(rows: list[dict]) -> bytes:
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    return b.getvalue().encode("utf-8")

def hash_archive_entry(z: zipfile.ZipFile, name: str) -> str:
    h = hashlib.sha256()
    with z.open(name) as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

index = []
with zipfile.ZipFile(source) as full:
    members = full.infolist()
    for run in runs:
        task_id = run["task_id"]
        prefix = f"tasks/{task_id}/"
        selected = [m for m in members if m.filename.startswith(prefix) and not m.is_dir()]
        names = {m.filename for m in selected}
        required = {
            prefix + "input/source.toml",
            prefix + "analysis_v151r081/frame_data.csv",
            prefix + f"analysis_v151r081/{task_id}.pdf",
            prefix + "review_compare_v151r081_v3/interaction_review.html",
            prefix + "review_compare_v151r081_v3/review_video.mp4",
            prefix + f"pdf_outline_v1/{task_id}__PSC_paths_outlined.pdf",
        }
        assert required <= names, (task_id, required - names)
        assert run["analyzed_frame_count"] == run["encoded_video_frames"] == "7200"
        qrows = [q for q in quality if q["task_id"] == task_id]
        assert len(qrows) == 2, task_id
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(run["source_toml"]).stem).strip("_")
        filename = f"{stem}__{task_id}__7200frames_PSC1.5.1.zip"
        target = output / filename
        if not target.exists():
            temporary = output / (filename + ".partial")
            if temporary.exists():
                temporary.unlink()
            with zipfile.ZipFile(temporary, "w", allowZip64=True) as single:
                for info in selected:
                    new = zipfile.ZipInfo(info.filename, info.date_time)
                    new.compress_type = zipfile.ZIP_STORED if info.filename.lower().endswith((".mp4", ".pdf", ".npz")) else zipfile.ZIP_DEFLATED
                    new.external_attr = info.external_attr
                    with full.open(info) as source_file, single.open(new, "w", force_zip64=True) as target_file:
                        shutil.copyfileobj(source_file, target_file, 8 * 1024 * 1024)
                for shared in ("README.md", "VERSION_CONTROL.json", "PROCESSOR_PARITY.json", "CODE_REPAIR.json"):
                    single.writestr(shared, full.read(shared), compress_type=zipfile.ZIP_DEFLATED)
                single.writestr("RUN_MANIFEST_this_run.csv", csv_bytes([run]), compress_type=zipfile.ZIP_DEFLATED)
                single.writestr("BEETLE_QUALITY_this_run.csv", csv_bytes(qrows), compress_type=zipfile.ZIP_DEFLATED)
                about = (
                    f"# Dyadic review package: {task_id}\n\n"
                    f"Source TOML: {run['source_toml']}\n"
                    f"Frames: {run['first_global_frame']} through {run['last_global_frame_inclusive']} inclusive (7,200 frames).\n"
                    "Open tasks/" + task_id + "/review_compare_v151r081_v3/interaction_review.html for synchronized RAW/PSC video review.\n"
                    "The analysis PDF, outlined-PSC PDF, per-frame CSVs, events and provenance are under tasks/" + task_id + "/.\n"
                    "PSC model 1.5.1; processor 0.8.1-group. Biological interpretations remain UNREVIEWED.\n"
                )
                single.writestr("ABOUT_THIS_RUN.md", about, compress_type=zipfile.ZIP_DEFLATED)
            os.replace(temporary, target)
        with zipfile.ZipFile(target) as check:
            assert check.testzip() is None, filename
            assert required <= set(check.namelist()), filename
            video_name = prefix + "review_compare_v151r081_v3/review_video.mp4"
            outline_name = prefix + f"pdf_outline_v1/{task_id}__PSC_paths_outlined.pdf"
            assert hash_archive_entry(check, video_name) == run["viewer_video_sha256"], filename
            assert hash_archive_entry(check, outline_name) == run["outlined_pdf_sha256"], filename
        index.append({
            "filename": filename,
            "task_id": task_id,
            "source_toml": run["source_toml"],
            "first_global_frame": run["first_global_frame"],
            "last_global_frame_inclusive": run["last_global_frame_inclusive"],
            "encoded_video_frames": run["encoded_video_frames"],
            "zip_bytes": target.stat().st_size,
            "zip_sha256": hashlib.file_digest(target.open("rb"), "sha256").hexdigest(),
            "entry_count": len(selected) + 7,
            "contains_html_video_regular_pdf_outlined_pdf_csv": "yes",
        })
        print(f"{len(index)}/99 {filename} {target.stat().st_size}", flush=True)

assert len(index) == 99 and len({r["filename"] for r in index}) == 99
assert len(list(output.glob("*.zip"))) == 99
with (output / "ZIP_INDEX.csv").open("w", newline="") as handle:
    w = csv.DictWriter(handle, fieldnames=list(index[0]))
    w.writeheader()
    w.writerows(index)
(output / "README.md").write_text(
    "# Individual 2026 dyadic fight review ZIPs\n\n"
    "Each of the 99 ZIP files is a complete standalone package for one eligible 7,200-frame run. "
    "It includes the source and submitted TOMLs, analysis PDF, outlined-PSC PDF, frame-by-frame and event CSVs, "
    "RAW/PSC HTML review, synchronized MP4, quality/provenance files, and per-run manifest and beetle-quality rows. "
    "Open ABOUT_THIS_RUN.md after extraction. PSC model 1.5.1; processor 0.8.1-group. "
    "These are derivatives of existing IDtracker trajectories; no IDtracker rerun occurred. "
    "The analyses remain UNREVIEWED. One no-blob TOML and four structurally incompatible TOMLs were excluded "
    "from the 99-run release. The source 99-run ZIP and original task directories remain untouched.\n\n"
    "ZIP_INDEX.csv maps each ZIP filename to the source TOML, frame window, byte size and SHA-256. "
    "Download any one ZIP over Firebird SFTP/SSH without downloading the whole 7.66 GB release.\n"
)
receipt = {
    "schema": "dyadic-2026-individual-run-zips-v1",
    "source_archive": str(source),
    "source_archive_sha256": json.loads((root / "RELEASE_RECEIPT.json").read_text())["archive_sha256"],
    "zip_count": 99,
    "total_zip_bytes": sum(x["zip_bytes"] for x in index),
    "all_zip_integrity_passed": True,
    "all_video_and_outlined_pdf_hashes_match_release_manifest": True,
    "frames_per_run": 7200,
    "psc_model_version": "1.5.1",
    "processor_version": "0.8.1-group",
    "review_status": "UNREVIEWED",
}
(output / "PACKAGE_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2), flush=True)
