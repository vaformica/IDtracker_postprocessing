"""Display-only review orientation and aspect-preserving video geometry.

Analysis coordinates, fungus numbering, and distance calculations stay in the
original IDtracker coordinate system. This module transforms only the review
video and its HTML overlay.
"""

from __future__ import annotations

import numpy as np

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 920


def _fungus_centers(rois) -> np.ndarray:
    centers = []
    for polygon in rois[1:]:
        points = np.asarray(polygon, dtype=float)
        if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3 or not np.isfinite(points).all():
            raise ValueError("Review ROI must be a finite polygon")
        centers.append(points.mean(axis=0))
    if not centers:
        raise ValueError("Review orientation requires at least one fungus ROI")
    return np.asarray(centers)


def rotation_for_fungus_one_left(rois, crop) -> tuple[int, str]:
    """Return clockwise degrees that place F1 left of the other fungi.

    With a single fungus ROI, the arena's long axis and F1's position relative
    to its center provide the orientation. A centered single fungus has no
    defensible left/right direction and retains the source orientation.
    """
    centers = _fungus_centers(rois)
    _, _, width, height = crop
    if len(centers) > 1:
        spread = np.ptp(centers, axis=0)
        vertical = spread[1] > spread[0]
        axis = 1 if vertical else 0
        delta = centers[0, axis] - np.mean(centers[1:, axis])
        if abs(delta) < max(spread[axis] * 0.1, 1):
            return 0, "fungus-one-order-ambiguous"
        if vertical:
            return (90 if delta > 0 else 270), "fungus-centroid-vertical"
        return (180 if delta > 0 else 0), "fungus-centroid-horizontal"

    center = centers[0]
    if height > width:
        delta = center[1] - (crop[1] + height / 2)
        if abs(delta) < height * 0.1:
            return 0, "single-fungus-centered"
        return (90 if delta > 0 else 270), "single-fungus-vertical-arena"
    delta = center[0] - (crop[0] + width / 2)
    if abs(delta) < width * 0.1:
        return 0, "single-fungus-centered"
    return (180 if delta > 0 else 0), "single-fungus-horizontal-arena"


def plan_review_geometry(rois, crop) -> dict:
    x, y, width, height = (int(v) for v in crop)
    if width <= 0 or height <= 0:
        raise ValueError("Review crop must have positive dimensions")
    rotation, reason = ((0, "single-arena-source-orientation") if len(rois) == 1
                        else rotation_for_fungus_one_left(rois, (x, y, width, height)))
    rotated_width, rotated_height = (height, width) if rotation in (90, 270) else (width, height)
    scale = min(CANVAS_WIDTH / rotated_width, CANVAS_HEIGHT / rotated_height)
    content_width = max(2, int(rotated_width * scale) // 2 * 2)
    content_height = max(2, int(rotated_height * scale) // 2 * 2)
    pad_x = (CANVAS_WIDTH - content_width) // 2
    pad_y = (CANVAS_HEIGHT - content_height) // 2
    return dict(crop=[x, y, width, height], rotation_cw=rotation,
                orientation_reason=reason, canvas_width=CANVAS_WIDTH,
                canvas_height=CANVAS_HEIGHT, content_width=content_width,
                content_height=content_height, pad_x=pad_x, pad_y=pad_y,
                aspect_preserved=True)


def legacy_review_geometry(crop) -> dict:
    """Describe old prepared videos without claiming their stretch was fixed."""
    x, y, width, height = (int(v) for v in crop)
    return dict(crop=[x, y, width, height], rotation_cw=0,
                orientation_reason="legacy-prepared-video", canvas_width=CANVAS_WIDTH,
                canvas_height=CANVAS_HEIGHT, content_width=CANVAS_WIDTH,
                content_height=CANVAS_HEIGHT, pad_x=0, pad_y=0,
                aspect_preserved=False)


def transform_point(point, geometry) -> tuple[float, float]:
    """Map original IDtracker x/y into the fixed review canvas."""
    x, y, width, height = geometry["crop"]
    dx, dy = point[0] - x, point[1] - y
    rotation = geometry["rotation_cw"]
    if rotation == 90:
        dx, dy = height - dy, dx
        width, height = height, width
    elif rotation == 180:
        dx, dy = width - dx, height - dy
    elif rotation == 270:
        dx, dy = dy, width - dx
        width, height = height, width
    elif rotation != 0:
        raise ValueError(f"Unsupported review rotation: {rotation}")
    return (geometry["pad_x"] + dx * geometry["content_width"] / width,
            geometry["pad_y"] + dy * geometry["content_height"] / height)


def review_filter(start: int, end: int, geometry: dict) -> str:
    x, y, width, height = geometry["crop"]
    filters = [f"trim=start_frame={start}:end_frame={end + 1}",
               "setpts=PTS-STARTPTS", f"crop={width}:{height}:{x}:{y}"]
    rotation = geometry["rotation_cw"]
    if rotation == 90:
        filters.append("transpose=clock")
    elif rotation == 180:
        filters.extend(("hflip", "vflip"))
    elif rotation == 270:
        filters.append("transpose=cclock")
    elif rotation != 0:
        raise ValueError(f"Unsupported review rotation: {rotation}")
    filters.extend((f"scale={geometry['content_width']}:{geometry['content_height']}:flags=lanczos",
                    f"pad={CANVAS_WIDTH}:{CANVAS_HEIGHT}:{geometry['pad_x']}:{geometry['pad_y']}:black",
                    "setsar=1"))
    return ",".join(filters)
