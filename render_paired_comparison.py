#!/usr/bin/env python3
"""Render the completed 2024 GroupTrial paired comparison as a two-page PDF."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


INK = colors.HexColor("#17283B")
MUTED = colors.HexColor("#506174")
HUMAN = colors.HexColor("#147D82")
SHARED = colors.HexColor("#E09336")
GRID = colors.HexColor("#D8E0E7")
PAPER = colors.HexColor("#F5F8FA")


def number(value: str | None, decimals: int = 1) -> str:
    return f"{float(value):.{decimals}f}" if value not in (None, "") else "--"


def short_label(source: str) -> str:
    stem = Path(source).stem
    return stem.replace("groupagetrial", "Trial ").replace("_062024_", " / ").replace("_062124_", " / ").replace("_", " ")


def text(canvas: Canvas, x: float, y: float, content: str, size: int = 10, color=INK, font="Helvetica") -> None:
    canvas.setFillColor(color)
    canvas.setFont(font, size)
    canvas.drawString(x, y, content)


def right(canvas: Canvas, x: float, y: float, content: str, size: int = 10, color=INK, font="Helvetica") -> None:
    canvas.setFillColor(color)
    canvas.setFont(font, size)
    canvas.drawRightString(x, y, content)


def header(canvas: Canvas, page: int, title: str) -> None:
    width, height = landscape(letter)
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(HUMAN)
    canvas.rect(0, height - 9, width, 9, fill=1, stroke=0)
    text(canvas, 40, 560, title, 20, INK, "Helvetica-Bold")
    text(canvas, 40, 540, "2024 GroupTrial | six beetles | five source TOMLs | background subtraction ON in both arms", 9, MUTED)
    canvas.setStrokeColor(GRID)
    canvas.line(40, 527, 752, 527)
    text(canvas, 40, 20, "IDtracker.ai output measures; identity continuity and presumed social contact require visual review.", 8, MUTED)
    right(canvas, 752, 20, f"{page} / 2", 8, MUTED)


def page_one(canvas: Canvas, pairs: list[dict]) -> None:
    header(canvas, 1, "Paired tracking settings: quantitative comparison")
    text(canvas, 40, 507, "Human settings retain each source's original intensity and blob area; shared settings use 50-255 and 400 px2.", 9)
    text(canvas, 40, 493, "Original start/end frames and all four ROIs are identical within each pair. End frame is exclusive.", 9)
    complete = sum(pair.get("human_missing_percent") not in (None, "") and pair.get("shared_missing_percent") not in (None, "") for pair in pairs)
    right(canvas, 752, 493, f"{complete} / {len(pairs)} pairs measured", 9, HUMAN, "Helvetica-Bold")

    headings = [(40, "Source / original settings"), (293, "Missing: human"), (397, "Missing: shared"), (506, "Change (pp)"), (600, "Est. ID H / C"), (749, ">100px H / C")]
    canvas.setFillColor(INK)
    canvas.roundRect(40, 455, 712, 23, 4, fill=1, stroke=0)
    for x, label in headings:
        if x == 749:
            right(canvas, x, 463, label, 8, colors.white, "Helvetica-Bold")
        else:
            text(canvas, x + (7 if x == 40 else 0), 463, label, 8, colors.white, "Helvetica-Bold")
    for i, pair in enumerate(pairs):
        y = 432 - i * 36
        if i % 2 == 0:
            canvas.setFillColor(colors.white)
            canvas.rect(40, y - 11, 712, 34, fill=1, stroke=0)
        source = short_label(pair["source_toml"])
        if stringWidth(source, "Helvetica-Bold", 9) > 245:
            source = source[:38] + "..."
        text(canvas, 47, y + 6, source, 9, INK, "Helvetica-Bold")
        settings = f"Start {pair['start_frame']} | {pair['human_intensity_low']}-{pair['human_intensity_high']} / {number(pair['human_area_min_px2'],0)} px2"
        text(canvas, 47, y - 7, settings, 8, MUTED)
        right(canvas, 372, y, number(pair.get("human_missing_percent")) + "%", 10, HUMAN, "Helvetica-Bold")
        right(canvas, 477, y, number(pair.get("shared_missing_percent")) + "%", 10, SHARED, "Helvetica-Bold")
        delta = pair.get("shared_minus_human_missing_percent")
        right(canvas, 570, y, ("--" if delta in (None, "") else f"{float(delta):+.1f}"), 10, INK)
        accuracy = number(pair.get("human_estimated_accuracy_percent")) + " / " + number(pair.get("shared_estimated_accuracy_percent"))
        right(canvas, 689, y + 4, accuracy, 8, INK)
        human_jumps = pair.get("human_jumps_over_100_px")
        shared_jumps = pair.get("shared_jumps_over_100_px")
        jumps = (human_jumps if human_jumps not in (None, "") else "--") + " / " + (shared_jumps if shared_jumps not in (None, "") else "--")
        right(canvas, 748, y - 8, jumps, 8, MUTED)
        canvas.setStrokeColor(GRID)
        canvas.line(40, y - 12, 752, y - 12)

    text(canvas, 40, 230, "Missing-coordinate rate by source", 12, INK, "Helvetica-Bold")
    text(canvas, 40, 216, "Bars use the same 0-100% scale. Lower is better for missingness; an identity estimate is not visual proof.", 8, MUTED)
    bar_left, bar_width = 277, 432
    canvas.setStrokeColor(GRID)
    for p in (0, 25, 50, 75, 100):
        x = bar_left + p / 100 * bar_width
        canvas.line(x, 47, x, 191)
        text(canvas, x - 6, 37, str(p), 7, MUTED)
    for i, pair in enumerate(pairs):
        y = 181 - 27 * i
        label = short_label(pair["source_toml"])
        text(canvas, 40, y, label[:40], 8, INK)
        for key, dy, color in (("human_missing_percent", 2, HUMAN), ("shared_missing_percent", -6, SHARED)):
            value = pair.get(key)
            if value not in (None, ""):
                canvas.setFillColor(color)
                canvas.rect(bar_left, y + dy, float(value) / 100 * bar_width, 6, fill=1, stroke=0)


def heat_color(value: float | None):
    if value is None:
        return colors.HexColor("#E4E9ED")
    magnitude = min(abs(value) / 40, 1)
    base = (0.08, 0.50, 0.51) if value < 0 else (0.88, 0.48, 0.16)
    return colors.Color(*(1 - (1 - channel) * (0.18 + 0.72 * magnitude) for channel in base))


def page_two(canvas: Canvas, beetles: list[dict], pairs: list[dict]) -> None:
    header(canvas, 2, "Which beetles changed?")
    text(canvas, 40, 507, "Each cell is shared minus human missing-coordinate percentage points. Green means fewer missing cells; orange means more.", 9)
    text(canvas, 40, 492, "Beetle IDs below are zero-based IDs from the raw trajectory array (0-5).", 9)
    grouped: dict[str, dict[int, dict]] = {}
    for row in beetles:
        grouped.setdefault(row["source_toml"], {})[int(row["beetle_id_zero_based"])] = row
    x0, cell_w = 278, 74
    for beetle in range(6):
        text(canvas, x0 + beetle * cell_w + 19, 451, f"ID {beetle}", 9, INK, "Helvetica-Bold")
    for i, pair in enumerate(pairs):
        source = pair["source_toml"]
        y = 402 - i * 61
        text(canvas, 40, y + 13, short_label(source)[:40], 9, INK, "Helvetica-Bold")
        text(canvas, 40, y - 2, f"Human {number(pair.get('human_missing_percent'))}%  |  Shared {number(pair.get('shared_missing_percent'))}%", 8, MUTED)
        for beetle in range(6):
            row = grouped[source][beetle]
            raw = row.get("shared_minus_human_pp")
            value = float(raw) if raw not in (None, "") else None
            x = x0 + beetle * cell_w
            canvas.setFillColor(heat_color(value))
            canvas.roundRect(x, y - 4, 64, 37, 4, fill=1, stroke=0)
            label = "--" if value is None else f"{value:+.1f}"
            color = INK if value is None or abs(value) < 25 else colors.white
            right(canvas, x + 56, y + 9, label, 10, color, "Helvetica-Bold")
    text(canvas, 40, 77, "Interpretation", 11, INK, "Helvetica-Bold")
    text(canvas, 40, 62, "Compare within each source only. Very sparse outputs can still have a high IDtracker estimated accuracy.", 8, MUTED)
    text(canvas, 40, 49, "Jumps count adjacent raw assigned coordinates >100 px, not movements reconstructed by the pile model.", 8, MUTED)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/pdf/GroupTrial_2024_paired_IDtracker_comparison.pdf"))
    args = parser.parse_args()
    with (args.batch_dir / "pairs.csv").open(newline="") as stream:
        pairs = list(csv.DictReader(stream))
    with (args.batch_dir / "per_beetle.csv").open(newline="") as stream:
        beetles = list(csv.DictReader(stream))
    if len(pairs) != 5 or len(beetles) != 30:
        raise ValueError("Expected five source pairs and 30 beetle rows")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(args.output), pagesize=landscape(letter))
    page_one(canvas, pairs)
    canvas.showPage()
    page_two(canvas, beetles, pairs)
    canvas.showPage()
    canvas.save()
    print(args.output)


if __name__ == "__main__":
    main()
