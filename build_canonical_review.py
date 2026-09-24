"""Build a portable synchronized review from a canonical analysis bundle."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from six_beetle_processor import regions


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean(value):
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, float):
        return round(value, 2) if np.isfinite(value) else None
    return value


def _safe_filename(name: str, suffix: str) -> str:
    if Path(name).name != name or not name.endswith(suffix):
        raise ValueError(f"Expected a plain {suffix} filename: {name!r}")
    return name


def _replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Review template changed: expected one occurrence of {old!r}, found {count}")
    return text.replace(old, new)


def build(
    bundle,
    video,
    output,
    crop,
    fps,
    label=None,
    html_name="interaction_review.html",
    video_name="review_video.mp4",
    link_video=False,
    initial_decisions=None,
):
    """Create a self-contained HTML/video review directory without overwriting."""
    bundle = Path(bundle)
    video = Path(video)
    output = Path(output)
    html_name = _safe_filename(html_name, ".html")
    video_name = _safe_filename(video_name, ".mp4")
    if output.exists():
        raise FileExistsError(f"Refusing existing output: {output}")
    if not video.is_file():
        raise FileNotFoundError(video)
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be finite and positive")
    x, y, width, height = map(float, crop)
    if not all(np.isfinite([x, y, width, height])) or width <= 0 or height <= 0:
        raise ValueError("crop must be finite x y width height with positive dimensions")

    manifest_path = bundle / "manifest.json"
    state_path = bundle / "canonical_states.npz"
    meta = json.loads(manifest_path.read_text())
    expected = meta.get("output_sha256", {}).get(state_path.name)
    if not expected or sha256(state_path) != expected:
        raise RuntimeError("Canonical state hash does not match the analysis manifest")

    data = np.load(state_path)
    xy = data["xy"]
    raw = data["raw"]
    if xy.ndim != 3 or xy.shape[1] < 2 or xy.shape[2] != 2:
        raise ValueError(f"Expected canonical shape (frames, animals, 2), found {xy.shape}")
    animal_count = xy.shape[1]
    frames = len(xy)
    start = int(meta["settings"]["start"])
    label = label or meta.get("cell_label") or Path(meta.get("video", "session")).stem
    roi_polygons = [np.asarray(polygon, float) for polygon in meta["rois"]]
    proximity_px = float(meta['settings'].get('social_distance_threshold_px', 60))
    max_step_px = float(meta.get('reconstruction', {}).get('max_speed_px_per_frame', 100))

    fungus = np.zeros(xy.shape[:2], dtype=int)
    for animal in range(animal_count):
        masks = regions(xy[:, animal], roi_polygons, 30, 30)
        for fungus_id in range(1, len(roi_polygons)):
            fungus[masks[f"fungus_{fungus_id}"], animal] = fungus_id

    pairs = list(itertools.combinations(range(animal_count), 2))
    pair_states = []
    for animal_a, animal_b in pairs:
        same_group = (
            (data["group_ids"][:, animal_a] == data["group_ids"][:, animal_b])
            & (data["group_ids"][:, animal_a] >= 0)
            & np.isfinite(xy[:, [animal_a, animal_b]]).all(axis=(1, 2))
        )
        pscp = same_group & (data["inferred"][:, animal_a] | data["inferred"][:, animal_b])
        unresolved = (
            (data["group_ids"][:, animal_a] == data["group_ids"][:, animal_b])
            & (data["group_ids"][:, animal_a] >= 0)
            & ~np.isfinite(xy[:, [animal_a, animal_b]]).all(axis=(1, 2))
        )
        assigned = (data["source"][:, animal_a] == "ASSIGNED") & (data["source"][:, animal_b] == "ASSIGNED")
        proximity = assigned & (np.linalg.norm(xy[:, animal_a] - xy[:, animal_b], axis=1) <= proximity_px)
        pair_states.append(np.where(pscp, 2, np.where(unresolved, 4, np.where(proximity, 1, 0))))

    zero = np.zeros(xy.shape[:2], dtype=int)
    accepted = data["source"] == "ASSIGNED"
    payload = dict(
        start=start,
        end=start + frames - 1,
        fps=float(fps),
        maxStep=max_step_px,
        proximityThreshold=proximity_px,
        modelSettings=meta.get('persistent_group_settings',{}),
        analysisManifestSha256=sha256(manifest_path),
        canonicalSha256=expected,
        raw=clean(raw),
        held=clean(xy),
        reviewed=zero.tolist(),
        reviewPartners=(zero - 1).tolist(),
        annotations=[],
        pileStatus=data["source"].tolist(),
        identityConflict=(data["identity_conflict"] if "identity_conflict" in data.files
                          else np.zeros(xy.shape[:2], bool)).astype(int).tolist(),
        accepted=accepted.astype(int).tolist(),
        rejected=(np.isfinite(raw).all(axis=2) & ~accepted).astype(int).tolist(),
        bridge=clean(xy),
        anchors=np.tile(np.arange(animal_count), (frames, 1)).tolist(),
        inferred=(data["source"] == "PSCP_BLOB").astype(int).tolist(),
        fungus=fungus.tolist(),
        pairs=pairs,
        pairStates=np.asarray(pair_states).tolist(),
        rois=clean(roi_polygons),
    )

    template = Path(__file__).with_name("interaction_review_template.html").read_text()
    editor_path = Path(__file__).with_name("review_editor.js")
    template_path = Path(__file__).with_name("interaction_review_template.html")
    editor = editor_path.read_text()
    editor = _replace_once(editor, "__INITIAL_DECISIONS__", json.dumps(initial_decisions or [], separators=(",", ":")).replace('<', '\\u003c'))
    template = _replace_once(template, "__EDITOR_SCRIPT__", editor)
    template = _replace_once(template, "2024 six-beetle battles — OLD review", f"{animal_count}-beetle review — {label}")
    template = _replace_once(template, "2024 six-beetle battles · OLD · synchronized interaction review", f"{animal_count}-beetle synchronized interaction review · {label}")
    template = _replace_once(template, "Pink: provisional user-reviewed contact.", "All positions come from the report bundle. UNREVIEWED: identity attribution remains uncertain.")
    template = template.replace("OLD_source_crop.mp4", video_name)
    template = _replace_once(template, "point(D.raw[t][D.anchors[t][a]])", "point(D.held[t][a])")
    template = _replace_once(
        template,
        "(p[0]-1600)*1280/1366,(p[1]-192)*920/982",
        f"(p[0]-{x})*1280/{width},(p[1]-{y})*920/{height}",
    )
    template = _replace_once(
        template,
        "D.rejected[t][a]?'<br>Raw candidate rejected':''",
        "D.identityConflict[t][a]?'<br>⚠ Raw/PSC identity conflict — review':D.rejected[t][a]?'<br>Raw candidate rejected':''",
    )
    template = template.replace(
        'No defensible location means MISSING or UNRESOLVED SPLIT.',
        'No defensible location means MISSING, UNRESOLVED SPLIT, DEPARTURE UNCERTAIN, or RAW PSC CONFLICT.',
    )
    template = template.replace("Math.round(v.currentTime*D.fps)", "Math.floor(v.currentTime*D.fps+0.0001)")
    template = template.replace("Math.round(m.mediaTime*D.fps)", "Math.floor(m.mediaTime*D.fps+0.0001)")
    template = _replace_once(
        template,
        'min="250" max="16997" value="250"',
        f'min="{start}" max="{start + frames - 1}" value="{start}"',
    )
    template = _replace_once(
        template,
        "a+(D.reviewed[t][a]?' reviewed PSCP':ok?'':' PSCP')",
        "a+(ok?'':D.pileStatus[t][a]==='PSCP_BLOB'?' PSCP':' estimated')",
    )
    template = _replace_once(
        template,
        "Reacquisition uses elapsed frames and three consistent candidate frames; it cannot prove identity.",
        "Group splits require three consistent assignments. Automatic identity inference cannot prove identity; review the video before approval.",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".six-beetle-review-", dir=output.parent))
    try:
        (staging / html_name).write_text(
            template.replace("__DATA__", json.dumps(payload, separators=(",", ":"), allow_nan=False))
        )
        destination_video = staging / video_name
        if link_video:
            os.symlink(video.resolve(), destination_video)
        else:
            try:
                os.link(video, destination_video)
            except OSError:
                shutil.copy2(video, destination_video)
        source_manifest = dict(
            schema="six-beetle-interaction-review-v1" if animal_count == 6 else "group-interaction-review-v1",
            status="HUMAN_REVIEWED_UNVERIFIED" if initial_decisions else "UNREVIEWED",
            decision_count=len(initial_decisions or []),
            review_code_sha256={"build_canonical_review.py":sha256(Path(__file__)),
                                "interaction_review_template.html":sha256(template_path),
                                "review_editor.js":sha256(editor_path)},
            animal_count=animal_count,
            fungus_count=len(roi_polygons)-1,
            label=label,
            analysis_bundle=str(bundle.resolve()),
            analysis_manifest_sha256=sha256(manifest_path),
            canonical_sha256=expected,
            video_source=str(video.resolve()),
            video_sha256=sha256(video),
            copied_video_sha256=sha256(destination_video),
            crop=[x, y, width, height],
            fps=float(fps),
            html=html_name,
            video=video_name,
        )
        (staging / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2) + "\n")
        os.rename(staging, output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output / html_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--crop", type=float, nargs=4, required=True, metavar=("X", "Y", "WIDTH", "HEIGHT"))
    parser.add_argument("--fps", type=float, required=True)
    parser.add_argument("--label")
    parser.add_argument("--html-name", default="interaction_review.html")
    parser.add_argument("--video-name", default="review_video.mp4")
    parser.add_argument("--link-video", action="store_true", help="Use a symlink instead of making a portable video file")
    args = parser.parse_args()
    print(build(**vars(args)))


if __name__ == "__main__":
    main()
