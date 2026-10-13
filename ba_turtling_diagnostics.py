"""Read-only gate audit of frozen BA candidates; never a posture classifier.

Run against the original scoring snapshot on Firebird. Single-gate ablations
are diagnostic counterfactuals, not proposed or validated detector settings.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

GATES = ("finite_fraction", "maximum_step", "path", "radius", "turns", "straightness")


def window_features(xy, window=120):
    xy = np.asarray(xy, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2 or window < 3:
        raise ValueError("Expected N by 2 coordinates and window >= 3")
    rows = []
    for first in range(max(0, len(xy) - window + 1)):
        block = xy[first:first + window]
        valid = np.isfinite(block).all(axis=1)
        vectors = np.diff(block, axis=0)
        lengths = np.linalg.norm(vectors, axis=1)
        steps = valid[:-1] & valid[1:]
        moving = steps & (lengths >= 1)
        path = float(lengths[moving].sum())
        points = block[valid]
        radius = (float(np.quantile(np.linalg.norm(points - np.median(points, axis=0), axis=1), .9))
                  if len(points) else np.nan)
        headings = np.arctan2(vectors[:, 1], vectors[:, 0])
        turns = np.arctan2(np.sin(np.diff(headings)), np.cos(np.diff(headings)))
        consecutive = moving[:-1] & moving[1:]
        rotations = float(np.abs(turns[consecutive]).sum() / (2 * np.pi))
        straightness = float(np.linalg.norm(points[-1] - points[0]) / path) if len(points) and path else np.inf
        rows.append((valid.mean(), float(lengths[steps].max()) if steps.any() else 0., path, radius, rotations, straightness))
    return np.asarray(rows, dtype=float).reshape(-1, 6)


def gate_passes(features):
    f = np.asarray(features)
    return np.column_stack((f[:, 0] >= .95, f[:, 1] <= 20, f[:, 2] >= 120,
                            (f[:, 3] >= 5) & (f[:, 3] <= 35), f[:, 4] >= 3, f[:, 5] <= .25))


def mask_from_windows(xy, accepted, window=120):
    """Union accepted windows while retaining every missing coordinate as missing."""
    delta = np.zeros(len(xy) + 1, dtype=int)
    starts = np.flatnonzero(accepted)
    np.add.at(delta, starts, 1)
    np.add.at(delta, starts + window, -1)
    return (np.cumsum(delta[:-1]) > 0) & np.isfinite(xy).all(axis=1)


def confusion(truth, predicted):
    return {"tp": int(np.sum(truth & predicted)), "fp": int(np.sum(~truth & predicted)),
            "tn": int(np.sum(~truth & ~predicted)), "fn": int(np.sum(truth & ~predicted))}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    root, scores, out = map(Path, (args.scoring_root, args.scores_dir, args.output))
    # Refuse to overwrite earlier evidence.
    out.mkdir(parents=True, exist_ok=False)
    receipt = json.loads((root / "VERIFICATION.json").read_text())
    def checked(relative):
        p = root / relative
        if sha(p) != receipt["hashes"][relative]:
            raise ValueError("Snapshot hash mismatch: " + relative)
        return json.loads(p.read_text())
    key = checked("selection_key.json")
    if sha(root / "code/processor.py") != key["baseline_code_sha256"]:
        raise ValueError("Frozen baseline code mismatch")
    sys.path.insert(0, str(root / "code"))
    import processor
    if Path(processor.__file__).resolve() != (root / "code/processor.py").resolve():
        raise ValueError("Must load the frozen processor")
    annotations = {}
    score_hashes = {}
    for part in range(1, 4):
        p = scores / f"scores_part_{part}_corrected.json"
        score_hashes[p.name] = sha(p)
        data = json.loads(p.read_text())
        if data["scoring_set"]["public_clips_sha256"] != sha(root / f"public_part_{part}.json"):
            raise ValueError("Score set mismatch")
        for a in data["annotations"]:
            if not a["complete"] or a["clip_id"] in annotations:
                raise ValueError("Incomplete or duplicate score")
            annotations[a["clip_id"]] = a
    if set(annotations) != {c["id"] for c in key["clips"]}:
        raise ValueError("Score IDs do not match selection")
    results = []
    for c in key["clips"]:
        s = key["sources"][c["source_index"]]
        if sha(s["trajectory"]) != s["trajectory_sha256"]:
            raise ValueError("Tracking input changed")
        xy = processor.load_trajectories(Path(s["trajectory"]))[c["start"]:c["end"] + 1, 0]
        if len(xy) != 7200:
            raise ValueError("Expected 7200 inclusive frames")
        features = window_features(xy)
        gates = gate_passes(features)
        reconstructed = mask_from_windows(xy, gates.all(axis=1))
        baseline = processor.compute_turtling_candidates(xy)["mask"]
        frozen = checked("predictions/" + c["id"] + ".json")
        saved = np.zeros(len(xy), dtype=bool)
        for b in frozen["baseline"]["bouts"]:
            saved[b["start_global_frame"]-c["start"]:b["end_global_frame_inclusive"]-c["start"]+1] = True
        if not np.array_equal(reconstructed, baseline) or not np.array_equal(saved, baseline):
            raise ValueError("Audit does not reproduce frozen baseline exactly")
        a = annotations[c["id"]]
        if (a["start_global_frame"], a["end_global_frame_inclusive"], a["fps"]) != (c["start"], c["end"], 30):
            raise ValueError("Human frame window mismatch")
        truth = np.zeros(len(xy), dtype=bool)
        for b in a["posture_intervals"]:
            lo, hi = b["first_global_frame"]-c["start"], b["last_global_frame"]-c["start"]+1
            if not 0 <= lo < hi <= len(xy) or truth[lo:hi].any():
                raise ValueError("Invalid human interval")
            truth[lo:hi] = True
        ablations = {}
        for i, name in enumerate(GATES):
            pred = mask_from_windows(xy, np.delete(gates, i, axis=1).all(axis=1))
            ablations[name] = confusion(truth, pred)
        np.savez_compressed(out / (c["id"] + ".npz"), xy=xy, features=features, gates=gates,
                            baseline=baseline, previous_experimental=np.asarray(frozen["episode_mask"]), truth=truth)
        results.append(dict(clip_id=c["id"], start=c["start"], role=c["role"],
                            baseline=confusion(truth, baseline),
                            previous_experimental=confusion(truth, np.asarray(frozen["episode_mask"])),
                            diagnostic_single_gate_removal=ablations))
        print(c["id"], "frozen baseline reproduced", flush=True)
    summary = dict(status="DIAGNOSTICS_ONLY_NOT_A_DETECTOR_REVISION", results=results,
                   feature_columns=list(GATES), score_hashes=score_hashes,
                   code_sha256=sha(__file__), note="All 12 scored runs are development data for any subsequent tuning.")
    (out / "GATE_AUDIT.json").write_text(json.dumps(summary, indent=2) + "\n")
    hashes = {p.name: sha(p) for p in out.iterdir() if p.is_file()}
    (out / "HASHES.json").write_text(json.dumps(hashes, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scoring-root", required=True)
    parser.add_argument("--scores-dir", required=True)
    parser.add_argument("--output", required=True)
    run(parser.parse_args())
