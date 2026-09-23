#!/usr/bin/env python3
"""Read paired Firebird trajectories and write an auditable quantitative comparison."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
from pathlib import Path

from idtracker_toml_manager import DEFAULT_IDTRACKER_ENV
from six_beetle_firebird_gui import DEFAULT_SSH_HOST, DEFAULT_SSH_KEY, SSH


REMOTE_METRICS = r'''
import hashlib,json,sys
from pathlib import Path
import numpy as np
batch=Path(json.load(sys.stdin)["batch_root"])
receipts=json.loads((batch/"batch_receipts.json").read_text())
rows=[]
for receipt in receipts:
    run=Path(receipt["run_dir"])
    status_path=run/"status.json"
    status=json.loads(status_path.read_text()) if status_path.is_file() else {}
    row={k:receipt.get(k) for k in ("job_id","variant","source_toml","source_sha256","submitted_toml_sha256","run_dir","tracking_intervals","intensity_ths","area_ths","use_bkg")}
    row["stage"]=status.get("stage","SUBMITTED")
    row["error"]=status.get("error","")
    sessions=list((run/"idtracker_output").glob("*/session.json"))
    if len(sessions)!=1:
        rows.append(row);continue
    session_path=sessions[0]
    trajectory_path=session_path.parent/"trajectories/trajectories.npy"
    if not trajectory_path.is_file():
        rows.append(row);continue
    saved=np.load(trajectory_path,allow_pickle=True)
    if saved.shape==():saved=saved.item()
    if isinstance(saved,dict):saved=saved.get("trajectories")
    points=np.asarray(saved)
    start,end=receipt["tracking_intervals"][0]
    if points.ndim!=3 or points.shape[1:]!=(6,2) or points.shape[0]<end or start>=end:
        row["error"]=f"Invalid trajectory shape {points.shape} for interval [{start},{end})"
        rows.append(row);continue
    window=points[start:end]
    valid=np.isfinite(window).all(axis=2)
    if not valid.any():
        row["error"]="No finite beetle positions in analysis interval"
        rows.append(row);continue
    session=json.loads(session_path.read_text())
    adjacent=valid[1:]&valid[:-1]
    movement=np.linalg.norm(np.diff(window,axis=0),axis=2)
    row.update(
        frames=end-start,
        missing_percent=float(100*(~valid).mean()),
        per_animal_missing_percent=[float(100*(~valid[:,i]).mean()) for i in range(6)],
        all_six_present_percent=float(100*valid.all(axis=1).mean()),
        eligible_adjacent_steps=int(adjacent.sum()),
        jumps_over_100_px=int((adjacent&(movement>100)).sum()),
        jumps_over_200_px=int((adjacent&(movement>200)).sum()),
        estimated_accuracy_percent=(float(100*session["estimated_accuracy"]) if isinstance(session.get("estimated_accuracy"),(int,float)) else None),
        number_of_error_frames=session.get("number_of_error_frames"),
        trajectory_sha256=hashlib.sha256(trajectory_path.read_bytes()).hexdigest(),
        session=str(session_path.parent),
        idtracker_version=session.get("version"),
    )
    rows.append(row)
json.dump(rows,sys.stdout,allow_nan=False)
'''


def fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row[key]) if isinstance(row.get(key), list) else row.get(key, "") for key in columns})


def render_report(rows: list[dict], batch_root: str) -> str:
    by_source: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_source.setdefault(Path(row["source_toml"]).stem, {})[row["variant"]] = row
    lines = [
        "# Paired IDtracker comparison: 2024 six-beetle battles",
        "",
        "Each source has two independent IDtracker runs. **Human + background** preserves its original threshold, blob area, start/end frames, and four ROIs while enabling background subtraction. **Shared 50/400** uses intensity 50–255, minimum area 400 px², and background subtraction, preserving that source's frame interval and ROIs. The source TOMLs were never overwritten.",
        "",
        "Missingness and jumps below use original IDtracker coordinates on the full specified tracking interval [start, end); presumed social contact positions are not substituted. A present IDtracker coordinate is not necessarily a direct visual detection. Estimated accuracy is IDtracker's estimate, not human identity validation. No failed run is assigned a zero-missingness score.",
        "",
        "| Source | Start–end (end exclusive) | Human missing % | Shared missing % | Shared − human (pp) | Human estimated accuracy % | Shared estimated accuracy % | Human jumps >100 px | Shared jumps >100 px | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    completed = 0
    for source, pair in sorted(by_source.items()):
        human = pair.get("human_bkg_on", {})
        shared = pair.get("shared_50_400_bkg_on", {})
        has_both = "missing_percent" in human and "missing_percent" in shared
        if has_both:
            completed += 1
        start_end = human.get("tracking_intervals", shared.get("tracking_intervals", [["?", "?"]]))[0]
        delta = shared["missing_percent"] - human["missing_percent"] if has_both else None
        status = "both measurable" if has_both else f"H: {human.get('stage','?')}; C: {shared.get('stage','?')}"
        lines.append(f"| {source} | {start_end[0]}–{start_end[1]} | {fmt(human.get('missing_percent'))} | {fmt(shared.get('missing_percent'))} | {fmt(delta)} | {fmt(human.get('estimated_accuracy_percent'))} | {fmt(shared.get('estimated_accuracy_percent'))} | {human.get('jumps_over_100_px','—')} | {shared.get('jumps_over_100_px','—')} | {status} |")
    lines += ["", f"Paired comparisons available: **{completed}/{len(by_source)}**.", "", "The shared setting should be judged across missingness, estimated accuracy, per-beetle results, and jump counts. Neither setting has been manually reviewed for identity continuity or pile interactions.", "", f"Firebird batch: `{batch_root}`. Detailed run and per-beetle metrics are in `runs.csv`; pairwise differences are in `pairs.csv`.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch_dir", type=Path, help="Local results/paired_... folder with submissions.json")
    parser.add_argument("--host", default=DEFAULT_SSH_HOST)
    parser.add_argument("--key", default=DEFAULT_SSH_KEY)
    args = parser.parse_args()
    receipts = json.loads((args.batch_dir / "submissions.json").read_text())
    batch_root = receipts[0]["batch_root"]
    ssh = SSH(args.host, args.key)
    command = shlex.quote(DEFAULT_IDTRACKER_ENV + "/bin/python") + " -c " + shlex.quote(REMOTE_METRICS)
    rows = json.loads(ssh.run(command, json.dumps({"batch_root": batch_root}), timeout=1800))
    run_columns = ["job_id","variant","source_toml","source_sha256","submitted_toml_sha256","run_dir","stage","error","tracking_intervals","intensity_ths","area_ths","use_bkg","frames","missing_percent","per_animal_missing_percent","all_six_present_percent","eligible_adjacent_steps","jumps_over_100_px","jumps_over_200_px","estimated_accuracy_percent","number_of_error_frames","trajectory_sha256","session","idtracker_version"]
    write_csv(args.batch_dir / "runs.csv", rows, run_columns)
    by_source: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_source.setdefault(row["source_toml"], {})[row["variant"]] = row
    pairs = []
    for source, group in sorted(by_source.items()):
        h, c = group.get("human_bkg_on", {}), group.get("shared_50_400_bkg_on", {})
        pair = {"source_toml": source, "human_job_id": h.get("job_id"), "shared_job_id": c.get("job_id"), "human_stage": h.get("stage"), "shared_stage": c.get("stage")}
        for key in ("missing_percent", "all_six_present_percent", "estimated_accuracy_percent", "jumps_over_100_px", "jumps_over_200_px"):
            pair["human_" + key] = h.get(key)
            pair["shared_" + key] = c.get(key)
            pair["shared_minus_human_" + key] = c[key] - h[key] if isinstance(h.get(key), (int, float)) and isinstance(c.get(key), (int, float)) else None
        pairs.append(pair)
    write_csv(args.batch_dir / "pairs.csv", pairs, list(pairs[0]))
    (args.batch_dir / "COMPARISON.md").write_text(render_report(rows, batch_root))
    print(f"{sum('missing_percent' in r for r in rows)}/{len(rows)} runs measurable; report: {args.batch_dir / 'COMPARISON.md'}")


if __name__ == "__main__":
    main()
