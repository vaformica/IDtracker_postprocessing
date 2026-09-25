#!/usr/bin/env python3
"""Add an immutable RAW/PSC comparison viewer to completed analysis tasks.

The existing analysis, PDF, CSV, source review, and tracking files are read
only. The new directory hardlinks the already-cropped review video when the
filesystem permits, so rebuilding the display does not rerun inference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_canonical_review import build, sha256

VIEW_VERSION = "raw-psc-compare-v1"
MODEL_VERSION = "1.5.1"
PROCESSOR_VERSION = "0.8.1-group"


def rebuild_task(root: Path, kind: str, task: dict) -> str:
    if kind == "grouptrial":
        label = Path(task["source_toml"]).stem
        folder = root / "tasks" / label
        status = folder / "status.json"
        analysis = folder / "analysis"
        review = folder / "review"
        output = folder / "review_compare"
    else:
        label = task["id"]
        folder = root / "tasks" / label
        status = folder / "status_v151r081.json"
        analysis = folder / "analysis_v151r081"
        review = folder / "review_v151r081"
        output = folder / "review_compare_v151r081"

    state = json.loads(status.read_text())
    if state.get("stage") != "COMPLETE_UNREVIEWED":
        return f"SKIPPED {label}: {state.get('stage', 'UNKNOWN')}"
    analysis_meta = json.loads((analysis / "manifest.json").read_text())
    if (analysis_meta.get("persistent_model_version") != MODEL_VERSION or
            analysis_meta.get("script_version") != PROCESSOR_VERSION or
            analysis_meta.get("qc_status") != "UNREVIEWED"):
        raise ValueError(f"Wrong analysis version or QC state: {label}")
    source = json.loads((review / "source_manifest.json").read_text())
    if source.get("analysis_manifest_sha256") != sha256(analysis / "manifest.json"):
        raise ValueError(f"Source review is bound to a different analysis: {label}")
    video = review / source["video"]
    if sha256(video) != source["copied_video_sha256"]:
        raise ValueError(f"Source review video hash mismatch: {label}")

    if output.exists():
        current = json.loads((output / "source_manifest.json").read_text())
        if (current.get("review_view_version") != VIEW_VERSION or
                current.get("analysis_manifest_sha256") != source["analysis_manifest_sha256"] or
                current.get("copied_video_sha256") != sha256(output / "review_video.mp4") or
                current.get("status") != "UNREVIEWED"):
            raise FileExistsError(f"Existing comparison review differs: {output}")
        return f"EXISTS {label}: {output}"

    build(analysis, video, output, source["crop"], source["fps"],
          label=source["label"])
    current = json.loads((output / "source_manifest.json").read_text())
    if (current["review_view_version"] != VIEW_VERSION or
            current["analysis_manifest_sha256"] != source["analysis_manifest_sha256"] or
            current["copied_video_sha256"] != source["copied_video_sha256"]):
        raise RuntimeError(f"Comparison viewer did not preserve provenance: {label}")
    return f"BUILT {label}: {output}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("grouptrial", "dyadic"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--task-id", help="One GroupTrial TOML stem or dyadic task ID")
    args = parser.parse_args()
    plan = json.loads((args.root / "plan.json").read_text())
    selected = [task for task in plan["tasks"] if
                args.task_id is None or
                (Path(task["source_toml"]).stem if args.kind == "grouptrial"
                 else task["id"]) == args.task_id]
    if not selected:
        parser.error(f"Task not in plan: {args.task_id}")
    for task in selected:
        print(rebuild_task(args.root, args.kind, task), flush=True)


if __name__ == "__main__":
    main()
