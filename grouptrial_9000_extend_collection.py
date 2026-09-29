#!/usr/bin/env python3
"""Verify and combine official 21 plus five corrected GroupTrial 9,000-frame runs."""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from grouptrial_9000_official_collection import check_row, sha


def build(official21: Path, added5: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    with (official21 / "RUN_MANIFEST.csv").open(newline="") as stream:
        old = list(csv.DictReader(stream))
    plan = json.loads((added5 / "plan.json").read_text())
    if len(old) != 21 or len(plan["tasks"]) != 5:
        raise ValueError("Expected verified official 21 and five corrected TOMLs")
    rows = []
    for item in old:
        rows.append(check_row(item["label"], Path(item["task_folder"]),
                              Path(item["source_toml"]), Path(item["submitted_toml"])))
    for item in plan["tasks"]:
        rows.append(check_row(item["label"], added5 / "tasks" / item["label"],
                              Path(item["source_toml"]), Path(item["submitted_toml"])))
    rows.sort(key=lambda x: x["label"])
    if len(rows) != 26 or len({x["label"] for x in rows}) != 26:
        raise ValueError("Combined collection does not have 26 distinct trials")
    for item in rows:
        task = Path(item["task_folder"])
        for pdf_path in (task / "analysis" / (item["label"] + ".pdf"),
                         next((task / "pdf_outline_v1").glob("*.pdf"))):
            content = subprocess.check_output(["pdftotext", str(pdf_path), "-"], text=True)
            if "1.5.1" not in content or "0.8.1-group" not in content:
                raise ValueError(f"PDF omits processor version: {pdf_path}")
    destination.mkdir(parents=True)
    (destination / "runs").mkdir()
    for item in rows:
        (destination / "runs" / item["label"]).symlink_to(item["task_folder"], target_is_directory=True)
    (destination / "README.md").write_text(
        "# Official 2024 GroupTrial six-beetle collection: 26 trials, 9,000 frames each\n\n"
        "The earlier 21 verified trials remain unchanged. Five corrected non-TEST "
        "TOMLs were submitted to IDtracker and then processed with PSC model 1.5.1 "
        "and processor 0.8.1-group. Each trial takes exactly the first 9,000 "
        "frames from its own TOML tracking start S, through S+8,999 inclusive. "
        "Every ZIP entry includes frame-level raw and PSC data, paired summaries, "
        "a regular PDF, an outlined-PSC PDF, and a 9,000-frame RAW/PSC comparison "
        "review video with HTML controls. All results are UNREVIEWED computational "
        "outputs. The TEST/TESTSAVE TOMLs are excluded, including the TESTSAVE "
        "file with no ROI or tracking interval. Source TOMLs and previous releases "
        "were not overwritten. The runs/ directory contains symlinks; the ZIP "
        "contains portable file copies. See RUN_MANIFEST.csv for every source, "
        "global frame interval, frame rate and content hash.\n"
    )
    with (destination / "RUN_MANIFEST.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    version = dict(schema="grouptrial-2024-9000-official-26-v1",
                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   official_trials=26, existing_trials=21, newly_tracked_trials=5,
                   frames_per_trial=9000, source_start_preserved=True,
                   psc_model_version="1.5.1", group_processor_version="0.8.1-group",
                   review_view_version="raw-psc-compare-v3",
                   pdf_track_style_version="outlined-psc-v1", qc_status="UNREVIEWED",
                   source_tomls_untouched=True, previous_release_untouched=True,
                   original_21_release=str(official21), newly_tracked_5_release=str(added5),
                   original_21_manifest_sha256=sha(official21 / "RUN_MANIFEST.csv"),
                   new_5_plan_sha256=sha(added5 / "plan.json"),
                   run_manifest_sha256=sha(destination / "RUN_MANIFEST.csv"),
                   collection_code_sha256=sha(Path(__file__)))
    repair = added5 / "CODE_REPAIR.json"
    if repair.is_file():
        shutil.copy2(repair, destination / "CODE_REPAIR.json")
        version["code_repair_sha256"] = sha(repair)
    parity = added5 / "PROCESSOR_PARITY.json"
    if not parity.is_file() or not json.loads(parity.read_text()).get("same_rule_code_and_parameters"):
        raise ValueError("Verified dyadic/six-beetle processor parity report is missing")
    shutil.copy2(parity, destination / "PROCESSOR_PARITY.json")
    version["processor_parity_report_sha256"] = sha(parity)
    (destination / "VERSION_CONTROL.json").write_text(json.dumps(version, indent=2) + "\n")
    archive = destination / "GroupTrial_2024_OFFICIAL_26_9000frames_PSC_v1.5.1_processor0.8.1.zip"
    with zipfile.ZipFile(archive, "w", allowZip64=True) as target:
        for name in ("README.md", "RUN_MANIFEST.csv", "VERSION_CONTROL.json",
                     "CODE_REPAIR.json", "PROCESSOR_PARITY.json"):
            if not (destination / name).is_file():
                continue
            target.write(destination / name, name)
        target.write(Path(__file__), "code/grouptrial_9000_extend_collection.py")
        for row in rows:
            label, task = row["label"], Path(row["task_folder"])
            target.write(row["source_toml"], f"{label}/source.toml")
            target.write(row["submitted_toml"], f"{label}/submitted.toml")
            for sub in ("analysis", "review_compare_v3", "pdf_outline_v1"):
                for path in sorted((task / sub).iterdir()):
                    if path.is_file():
                        method = zipfile.ZIP_STORED if path.suffix in (".mp4", ".pdf", ".npz") else zipfile.ZIP_DEFLATED
                        target.write(path, f"{label}/{sub}/{path.name}", compress_type=method)
            for name in ("status.json", "tracking_status.json", "analysis_status.json",
                         "video_probe.json", "analysis.pipeline_receipt.json"):
                path = task / name
                if path.is_file():
                    target.write(path, f"{label}/{name}")
    with zipfile.ZipFile(archive) as target:
        bad = target.testzip()
        if bad is not None:
            raise ValueError(f"Corrupt ZIP member: {bad}")
    receipt = dict(version, archive=str(archive), archive_sha256=sha(archive),
                   archive_bytes=archive.stat().st_size, zip_integrity_passed=True)
    (destination / "RELEASE_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: grouptrial_9000_extend_collection.py OFFICIAL21 NEW5 DESTINATION")
    build(*(Path(x) for x in sys.argv[1:]))
