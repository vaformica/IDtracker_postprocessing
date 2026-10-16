"""Build a portable synchronized review from a canonical analysis bundle."""

from __future__ import annotations

import argparse
import hashlib
import html
import itertools
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

import numpy as np

from six_beetle_processor import regions
from review_geometry import CANVAS_HEIGHT, CANVAS_WIDTH, legacy_review_geometry


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


def artifact_stem(source_toml, label):
    """Keep the complete original TOML stem, including its arena/cell suffix."""
    stem = Path(str(source_toml)).stem if source_toml else str(label)
    if not stem or Path(stem).name != stem or '\\' in stem or stem in ('.', '..'):
        raise ValueError('Artifact label must be a plain filename stem')
    return stem


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
    html_name=None,
    video_name=None,
    link_video=False,
    initial_decisions=None,
    video_geometry=None,
    source_video=None,
    video_filter=None,
    source_toml=None,
):
    """Create a self-contained HTML/video review directory without overwriting."""
    bundle = Path(bundle)
    video = Path(video)
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing existing output: {output}")
    if not video.is_file():
        raise FileNotFoundError(video)
    source_video = Path(source_video) if source_video is not None else video
    if not source_video.is_file():
        raise FileNotFoundError(source_video)
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be finite and positive")
    x, y, width, height = map(float, crop)
    if not all(np.isfinite([x, y, width, height])) or width <= 0 or height <= 0:
        raise ValueError("crop must be finite x y width height with positive dimensions")
    video_geometry = video_geometry or legacy_review_geometry(crop)
    if (video_geometry.get('crop') != [int(x), int(y), int(width), int(height)] or
            video_geometry.get('canvas_width') != CANVAS_WIDTH or
            video_geometry.get('canvas_height') != CANVAS_HEIGHT or
            video_geometry.get('rotation_cw') not in (0, 90, 180, 270)):
        raise ValueError('Video geometry does not match the review crop and canvas')

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
    source_toml = str(source_toml or meta.get('source_toml') or '')
    stem = artifact_stem(source_toml, label)
    html_name = _safe_filename(html_name or f'{stem}__interaction_review.html', '.html')
    video_name = _safe_filename(video_name or f'{stem}__review_video.mp4', '.mp4')
    # The recording name is shared by several cells. Never let a custom
    # display label replace the identity carried by the source TOML.
    toml_name = Path(source_toml).name if source_toml else ''
    cell_match = re.search(r'_(Box\d+|[A-Z]\d+)(?:_(?:OLD|MIX|YOUNG))?$', Path(toml_name).stem, re.IGNORECASE)
    cell_id = cell_match.group(1).upper() if cell_match else ''
    identity_text = (f'Cell: {cell_id or "not recorded"} · Source TOML: '
                     f'{toml_name or "not recorded"}')
    roi_polygons = [np.asarray(polygon, float) for polygon in meta["rois"]]
    proximity_px = float(meta['settings'].get('social_distance_threshold_px', 60))
    max_step_px = float(meta.get('reconstruction', {}).get('max_speed_px_per_frame', 100))

    fungus = np.zeros(xy.shape[:2], dtype=int)
    raw_fungus = np.zeros(raw.shape[:2], dtype=int)
    for animal in range(animal_count):
        masks = regions(xy[:, animal], roi_polygons, 30, 30)
        raw_masks = regions(raw[:, animal], roi_polygons, 30, 30)
        for fungus_id in range(1, len(roi_polygons)):
            fungus[masks[f"fungus_{fungus_id}"], animal] = fungus_id
            raw_fungus[raw_masks[f"fungus_{fungus_id}"], animal] = fungus_id

    pairs = list(itertools.combinations(range(animal_count), 2))
    pair_states = []
    raw_pair_states = []
    for animal_a, animal_b in pairs:
        raw_pair_states.append((np.isfinite(raw[:, [animal_a, animal_b]]).all(axis=(1, 2))
                                & (np.linalg.norm(raw[:, animal_a] - raw[:, animal_b], axis=1)
                                   <= proximity_px)).astype(int))
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
        cellId=cell_id or None,
        sourceToml=source_toml or None,
        start=start,
        end=start + frames - 1,
        fps=float(fps),
        maxStep=max_step_px,
        proximityThreshold=proximity_px,
        modelSettings=meta.get('persistent_group_settings',{}),
        pscModelVersion=meta.get('persistent_model_version', 'unknown'),
        processorVersion=meta.get('script_version', 'unknown'),
        reviewViewVersion='raw-psc-compare-v4',
        videoGeometry=video_geometry,
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
        rawFungus=raw_fungus.tolist(),
        pairs=pairs,
        pairStates=np.asarray(pair_states).tolist(),
        rawPairStates=np.asarray(raw_pair_states).tolist(),
        rois=clean(roi_polygons),
    )

    template = Path(__file__).with_name("interaction_review_template.html").read_text()
    editor_path = Path(__file__).with_name("review_editor.js")
    template_path = Path(__file__).with_name("interaction_review_template.html")
    editor = editor_path.read_text()
    editor = _replace_once(editor, "__INITIAL_DECISIONS__", json.dumps(initial_decisions or [], separators=(",", ":")).replace('<', '\\u003c'))
    template = _replace_once(template, "__EDITOR_SCRIPT__", editor)
    display_label = html.escape(str(label))
    cell_title = f'Cell {cell_id} · ' if cell_id else ''
    template = _replace_once(template, "2024 six-beetle battles — OLD review", f"{cell_title}{animal_count}-beetle review — {display_label}")
    template = _replace_once(template, "2024 six-beetle battles · OLD · synchronized interaction review", f"{cell_title}{animal_count}-beetle synchronized interaction review · {display_label}")
    template = _replace_once(template, '</h1>', '</h1>\n<p id="recordingIdentity">'+html.escape(identity_text)+'</p>')
    template = _replace_once(template, "Pink: provisional user-reviewed contact.", "All positions come from the report bundle. UNREVIEWED: identity attribution remains uncertain.")
    template = template.replace("OLD_source_crop.mp4", html.escape(video_name, quote=True))
    template = _replace_once(template, "point(D.raw[t][D.anchors[t][a]])", "point(D.held[t][a])")
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
        ("Available IDs remain assigned, including after separation and when sharing a blob. PSC applies only to missing IDs; review inferred positions before approval."
         if meta.get("raw_identity_policy") == "IDTRACKER_AUTHORITATIVE" else
         "Group splits require three consistent assignments. Automatic identity inference cannot prove identity; review the video before approval."),
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".six-beetle-review-", dir=output.parent))
    try:
        (staging / html_name).write_text(
            template.replace("__DATA__", json.dumps(payload, separators=(",", ":"), allow_nan=False).replace('<', '\\u003c'))
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
            schema="six-beetle-interaction-review-v2" if animal_count == 6 else "group-interaction-review-v2",
            review_view_version='raw-psc-compare-v4',
            analysis_frame_count=frames,
            psc_model_version=meta.get('persistent_model_version', 'unknown'),
            processor_version=meta.get('script_version', 'unknown'),
            status="HUMAN_REVIEWED_UNVERIFIED" if initial_decisions else "UNREVIEWED",
            decision_count=len(initial_decisions or []),
            review_code_sha256={"build_canonical_review.py":sha256(Path(__file__)),
                                "review_geometry.py":sha256(Path(__file__).with_name('review_geometry.py')),
                                "interaction_review_template.html":sha256(template_path),
                                "review_editor.js":sha256(editor_path)},
            animal_count=animal_count,
            fungus_count=len(roi_polygons)-1,
            label=label,
            cell_id=cell_id or None,
            source_toml=source_toml or None,
            analysis_bundle=str(bundle.resolve()),
            analysis_manifest_sha256=sha256(manifest_path),
            canonical_sha256=expected,
            video_source=str(source_video.resolve()),
            video_sha256=sha256(source_video),
            copied_video_sha256=sha256(destination_video),
            video_generation_filter=video_filter,
            crop=[x, y, width, height],
            video_geometry=video_geometry,
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
    parser.add_argument("--source-toml")
    parser.add_argument("--html-name")
    parser.add_argument("--video-name")
    parser.add_argument("--link-video", action="store_true", help="Use a symlink instead of making a portable video file")
    args = parser.parse_args()
    print(build(**vars(args)))


if __name__ == "__main__":
    main()
