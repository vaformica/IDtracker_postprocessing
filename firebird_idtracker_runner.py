#!/usr/bin/env python3
"""Run one immutable IDtracker.ai TOML and leave machine-readable status."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def status(root: Path, stage: str, **details) -> None:
    payload = {
        "stage": stage,
        "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        **details,
    }
    atomic_json(root / "status.json", payload)
    print(json.dumps(payload, sort_keys=True), flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toml", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--data-policy", default="all")
    args = parser.parse_args(argv)

    root = Path.cwd()
    log_path = root / "idtracker.log"
    try:
        if not args.toml.is_file():
            raise FileNotFoundError(args.toml)
        args.output.mkdir(parents=True, exist_ok=False)
        if args.device == "cuda":
            subprocess.run(
                [sys.executable, "-c", "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"],
                check=True,
            )
        executable = Path(sys.executable).with_name("idtrackerai")
        command = [
            str(executable),
            "--track",
            "--load",
            str(args.toml),
            "--output_dir",
            str(args.output),
            "--number_of_parallel_workers",
            str(args.workers),
            "--device",
            args.device,
            "--data_policy",
            args.data_policy,
        ]
        status(root, "TRACKING", command=command, toml=str(args.toml), output=str(args.output))
        with log_path.open("x") as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True, cwd=root)
        sessions = sorted(str(path.parent) for path in args.output.rglob("session.json"))
        if not sessions:
            raise RuntimeError("IDtracker.ai exited successfully but produced no session.json")
        status(root, "COMPLETE_UNREVIEWED", sessions=sessions, log=str(log_path))
        return 0
    except BaseException as exc:
        status(root, "FAILED", error=repr(exc), log=str(log_path))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
