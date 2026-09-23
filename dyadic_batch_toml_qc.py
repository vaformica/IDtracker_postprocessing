#!/usr/bin/env python3
"""Flag suspicious student ROI geometry in the staged 2026 dyadic TOMLs.

These are review flags, not grounds for silently changing an input or dropping
a completed result. Structural exclusions are recorded in plan.json.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import tomllib
from pathlib import Path


def polygon(text: str) -> list[tuple[float, float]]:
    if not text.startswith('+ Polygon '):
        raise ValueError('ROI is not an additive polygon')
    points = ast.literal_eval(text[len('+ Polygon '):])
    if len(points) < 3:
        raise ValueError('Polygon has fewer than 3 vertices')
    return [(float(x), float(y)) for x, y in points]


def area(points: list[tuple[float, float]]) -> float:
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2)
                   in zip(points, points[1:] + points[:1]))) / 2


def inside(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    result = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1:
            result = not result
    return result


def inspect(task: dict, root: Path) -> dict:
    path = root / 'tasks' / task['id'] / 'input' / 'submitted.toml'
    data = tomllib.loads(path.read_text())
    flags = []
    try:
        arena, fungus = (polygon(item) for item in data['roi_list'])
        arena_area, fungus_area = area(arena), area(fungus)
        if not all(math.isfinite(v) for p in arena + fungus for v in p):
            flags.append('nonfinite_roi_coordinate')
        if arena_area <= 0 or fungus_area <= 0:
            flags.append('zero_area_roi')
        if arena_area and fungus_area/arena_area > 0.5:
            flags.append('fungus_larger_than_half_arena')
        if arena_area and fungus_area/arena_area < 0.001:
            flags.append('fungus_smaller_than_0.1_percent_arena')
        centroid = (sum(x for x, _ in fungus)/len(fungus),
                    sum(y for _, y in fungus)/len(fungus))
        if not inside(centroid, arena):
            flags.append('fungus_centroid_outside_arena')
        outside = sum(not inside(point, arena) for point in fungus)
        if outside / len(fungus) > 0.25:
            flags.append('more_than_quarter_fungus_vertices_outside_arena')
    except (ValueError, SyntaxError, TypeError, KeyError) as exc:
        arena_area = fungus_area = None
        flags.append(f'roi_parse_error:{exc}')
    return dict(task_id=task['id'], source_path=task['source_path'],
                source_sha256=task['source_sha256'], arena_area_px2=arena_area,
                fungus_area_px2=fungus_area, warnings=';'.join(flags))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    plan = json.loads((args.root / 'plan.json').read_text())
    rows = [inspect(task, args.root) for task in plan['tasks']]
    target = args.root / 'reports' / 'toml_geometry_qc.csv'
    target.parent.mkdir(exist_ok=True)
    with target.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(dict(inspected=len(rows), flagged=sum(bool(row['warnings']) for row in rows),
                          flagged_tasks=[row for row in rows if row['warnings']]), indent=2))


if __name__ == '__main__':
    main()
