#!/usr/bin/env python3
"""Pure helpers and remote scripts for the Firebird TOML submission GUI."""

from __future__ import annotations

import hashlib
import json
import math
import re
import tomllib
from pathlib import PurePosixPath


DEFAULT_GROUPTRIAL_ROOT = "/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024"
DEFAULT_RUN_ROOT = f"{DEFAULT_GROUPTRIAL_ROOT}/managed_idtracker_runs"
DEFAULT_IDTRACKER_ENV = "/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14"


REMOTE_TOML_INVENTORY = r'''
import datetime,hashlib,json,sys,tomllib
import math
from pathlib import Path

request=json.load(sys.stdin)
records=[]
def safe(value):
    if isinstance(value,float) and not math.isfinite(value):
        return "inf" if value > 0 else "-inf"
    if isinstance(value,list):return [safe(x) for x in value]
    if isinstance(value,dict):return {str(k):safe(v) for k,v in value.items()}
    return value
for root_text in request.get("roots",[]):
    root=Path(root_text).expanduser()
    if not root.is_dir():continue
    for path in root.rglob("*.toml"):
        if path.name.startswith("._"):continue
        try:
            raw=path.read_bytes(); data=tomllib.loads(raw.decode("utf-8"))
            animals=data.get("number_of_animals")
            rois=data.get("roi_list"); roi_count=len(rois) if isinstance(rois,list) else 0
            videos=data.get("video_paths") or []
            if isinstance(videos,str):videos=[videos]
            intervals=data.get("tracking_intervals")
            rel=path.relative_to(root)
            parts=set(rel.parts)
            if any(p.startswith("six_beetle_grid_") for p in rel.parts):kind="sweep"
            elif "six_beetle_runs" in parts or "managed_idtracker_runs" in parts:kind="previous run"
            elif path.parent == root:kind="original"
            else:kind="other"
            stat=path.stat()
            records.append({
                "path":str(path),"root":str(root),"relative":str(rel),"filename":path.name,
                "kind":kind,"name":str(data.get("name",path.stem)),"animals":animals,
                "roi_count":roi_count,"eligible":animals==6 and roi_count==4,
                "intensity":safe(data.get("intensity_ths")),"area":safe(data.get("area_ths")),
                "intervals":safe(intervals),"use_bkg":data.get("use_bkg"),
                "background_stat":data.get("background_subtraction_stat"),
                "videos":videos,"video_exists":bool(videos) and all(Path(v).is_file() for v in videos),
                "sha256":hashlib.sha256(raw).hexdigest(),"size":stat.st_size,
                "modified_utc":datetime.datetime.fromtimestamp(stat.st_mtime,datetime.timezone.utc).isoformat(),
                "error":"",
            })
        except Exception as exc:
            records.append({"path":str(path),"root":str(root),"relative":str(path.relative_to(root)),
                "filename":path.name,"kind":"invalid","name":path.stem,"animals":None,"roi_count":0,
                "eligible":False,"intensity":None,"area":None,"intervals":None,"use_bkg":None,
                "background_stat":None,"videos":[],"video_exists":False,"sha256":"","size":0,
                "modified_utc":"","error":repr(exc)})
records.sort(key=lambda r:(r["kind"]!="original",r["relative"].lower()))
json.dump(records,sys.stdout,allow_nan=False)
'''


def parse_toml(text: str) -> dict:
    return tomllib.loads(text)


def validate_six_beetle_toml(text: str) -> dict:
    data = parse_toml(text)
    animals = data.get("number_of_animals")
    rois = data.get("roi_list")
    videos = data.get("video_paths")
    if animals != 6:
        raise ValueError(f"number_of_animals must be 6; found {animals!r}")
    if not isinstance(rois, list) or len(rois) != 4:
        count = len(rois) if isinstance(rois, list) else 0
        raise ValueError(f"roi_list must contain the arena plus three fungus ROIs; found {count}")
    if not isinstance(videos, list) or not videos or not all(isinstance(x, str) and x.strip() for x in videos):
        raise ValueError("video_paths must contain at least one nonblank Firebird path")
    return data


def _toml_number(value: str | float | int) -> str:
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"inf", "+inf"}:
            return "inf"
        if stripped == "-inf":
            return "-inf"
        value = float(stripped)
    number = float(value)
    if not math.isfinite(number):
        return "inf" if number > 0 else "-inf"
    return str(int(number)) if number.is_integer() else repr(number)


def _value_span(lines: list[str], key: str) -> tuple[int, int]:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for start, line in enumerate(lines):
        if not pattern.match(line):
            continue
        rhs = line.split("=", 1)[1]
        balance = rhs.count("[") - rhs.count("]")
        end = start + 1
        while balance > 0 and end < len(lines):
            balance += lines[end].count("[") - lines[end].count("]")
            end += 1
        return start, end
    raise KeyError(f"TOML has no top-level {key!r} field")


def update_common_fields(text: str, values: dict) -> str:
    """Replace common top-level values while retaining ROI text and extra settings."""
    replacements = {
        "name": json.dumps(values["name"]),
        "video_paths": "[" + ", ".join(json.dumps(x) for x in values["video_paths"]) + "]",
        "intensity_ths": f"[{_toml_number(values['intensity_min'])}, {_toml_number(values['intensity_max'])}]",
        "area_ths": f"[{_toml_number(values['area_min'])}, {_toml_number(values['area_max'])}]",
        "tracking_intervals": f"[[{int(values['start'])}, {int(values['end'])}]]",
        "number_of_animals": str(int(values["animals"])),
        "use_bkg": "true" if bool(values["use_bkg"]) else "false",
    }
    lines = text.splitlines(keepends=True)
    for key, rendered in replacements.items():
        start, end = _value_span(lines, key)
        newline = "\n" if lines[end - 1].endswith("\n") else ""
        lines[start:end] = [f"{key} = {rendered}{newline}"]
    result = "".join(lines)
    validate_six_beetle_toml(result)
    return result


def common_fields(text: str) -> dict:
    data = parse_toml(text)
    intensity = data.get("intensity_ths") or ["", ""]
    area = data.get("area_ths") or ["", ""]
    intervals = data.get("tracking_intervals") or [["", ""]]
    first = intervals[0] if isinstance(intervals, list) and intervals and isinstance(intervals[0], list) else ["", ""]
    videos = data.get("video_paths") or []
    if isinstance(videos, str):
        videos = [videos]
    return {
        "name": data.get("name", ""),
        "video_paths": videos,
        "intensity_min": intensity[0], "intensity_max": intensity[1],
        "area_min": area[0], "area_max": area[1],
        "start": first[0], "end": first[1],
        "animals": data.get("number_of_animals", ""),
        "use_bkg": bool(data.get("use_bkg", False)),
        "roi_count": len(data.get("roi_list")) if isinstance(data.get("roi_list"), list) else 0,
    }


def safe_label(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return cleaned[:80] or "six_beetle"


def submission_command(environment: str, runner: str, toml: str, output: str, workers: int = 16) -> list[str]:
    return [
        str(PurePosixPath(environment) / "bin" / "python"), runner,
        "--toml", toml, "--output", output,
        "--workers", str(workers), "--device", "cuda", "--data-policy", "all",
    ]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
