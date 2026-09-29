#!/usr/bin/env python3
"""Prove shared PSC rule-code and parameter parity across current releases."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

MODEL = "1.5.1"
PROCESSOR = "0.8.1-group"
FILES = ("persistent_groups.py", "six_beetle_processor.py", "frame_data.py",
         "run_group_pipeline.py", "run_six_beetle_pipeline.py",
         "output_manifest.py", "render_psc_outlined_pdf.py",
         "build_canonical_review.py", "interaction_review_template.html")
PSC_KEYS = ("social_radius_px", "max_step_px_per_frame", "split_confirmation_frames",
            "gap_speed_px_per_frame", "gap_radius_cap_px", "max_reacquire_gap_frames",
            "distant_confirmation_frames", "unresolved_multiway_split_policy")
SETTING_KEYS = ("social_distance_threshold_px", "jump_threshold_px")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def manifest_parameters(path: Path) -> dict:
    manifest = json.loads(path.read_text())
    if (manifest.get("persistent_model_version") != MODEL or
            manifest.get("script_version") != PROCESSOR):
        raise ValueError(f"Wrong processor version: {path}")
    result = dict(model=manifest["persistent_model_version"],
                  processor=manifest["script_version"],
                  psc={key: manifest["persistent_group_settings"][key] for key in PSC_KEYS},
                  settings={key: manifest["settings"][key] for key in SETTING_KEYS})
    pdf = path.parent / manifest["pdf_filename"]
    extracted = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
    if MODEL not in extracted or PROCESSOR not in extracted:
        raise ValueError(f"PDF omits PSC/processor version: {pdf}")
    result.update(pdf=str(pdf), pdf_sha256=sha(pdf), pdf_version_text_verified=True)
    return result


def audit(code_roots: list[Path], group_manifest: Path, dyadic_plan: Path,
          group_pilot_manifest: Path, dyadic_pilot_manifest: Path, output: Path) -> dict:
    if len(code_roots) != 4:
        raise ValueError("Specify dyadic current, group new, group old, and group Box01 code snapshots")
    hashes = {}
    for name in FILES:
        values = {str(root): sha(root / name) for root in code_roots}
        if len(set(values.values())) != 1:
            raise ValueError(f"Code differs across releases: {name}: {values}")
        hashes[name] = next(iter(values.values()))
    with group_manifest.open(newline="") as stream:
        group_rows = list(csv.DictReader(stream))
    dyadic_tasks = [task for task in json.loads(dyadic_plan.read_text())["tasks"] if not task["excluded"]]
    if len(group_rows) != 21 or len(dyadic_tasks) != 99:
        raise ValueError("Unexpected baseline GroupTrial/dyadic counts")
    group = [manifest_parameters(Path(row["task_folder"]) / "analysis" / "manifest.json")
             for row in group_rows]
    group_pilot = manifest_parameters(group_pilot_manifest)
    dyadic_pilot = manifest_parameters(dyadic_pilot_manifest)
    reference = group[0]
    for result in group + [group_pilot, dyadic_pilot]:
        if (result["psc"], result["settings"]) != (reference["psc"], reference["settings"]):
            raise ValueError("Analyzed PSC parameters differ between batches")
    for task in dyadic_tasks:
        selected = task["persistent_group_settings"]
        settings = task["settings"]
        if (any(selected[key] != reference["psc"][key] for key in PSC_KEYS) or
                any(settings[key] != reference["settings"][key] for key in SETTING_KEYS)):
            raise ValueError(f"Dyadic plan has different PSC parameters: {task['id']}")
    report = dict(schema="shared-psc-processor-parity-v1",
                  created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  psc_model_version=MODEL, group_processor_version=PROCESSOR,
                  same_rule_code_and_parameters=True,
                  note="The same rules and values apply to two- and six-beetle runs. Different animal counts and ROI geometries can produce different contact patterns; this is code/parameter parity, not biological equivalence.",
                  code_snapshots=[str(root) for root in code_roots],
                  code_sha256=hashes, psc_parameters=reference["psc"],
                  shared_settings=reference["settings"],
                  prior_group_trial_count=len(group),
                  eligible_dyadic_task_count=len(dyadic_tasks),
                  newly_analyzed_group_pilot_manifest=str(group_pilot_manifest),
                  newly_analyzed_dyadic_pilot_manifest=str(dyadic_pilot_manifest),
                  version_in_every_checked_pdf=True,
                  data_version_location="Each analysis/manifest.json records persistent_model_version, script_version, settings, source hashes, and PDF style. Batch run/quality tables repeat processor versions.",
                  example_pdfs=dict(group=group_pilot["pdf"], dyadic=dyadic_pilot["pdf"]))
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("group21_manifest", type=Path)
    parser.add_argument("dyadic_plan", type=Path)
    parser.add_argument("group_pilot_manifest", type=Path)
    parser.add_argument("dyadic_pilot_manifest", type=Path)
    parser.add_argument("code_roots", type=Path, nargs=4)
    args = parser.parse_args()
    report = audit(args.code_roots, args.group21_manifest, args.dyadic_plan,
                   args.group_pilot_manifest, args.dyadic_pilot_manifest, args.output)
    print(json.dumps({"same_rule_code_and_parameters": report["same_rule_code_and_parameters"],
                      "model": MODEL, "processor": PROCESSOR,
                      "group_trials": report["prior_group_trial_count"],
                      "dyadic_tasks": report["eligible_dyadic_task_count"]}), flush=True)


if __name__ == "__main__":
    main()
