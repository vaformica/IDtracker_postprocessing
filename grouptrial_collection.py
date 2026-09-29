"""Build a single, version-gated index for the two GroupTrial releases.

The full release ZIPs are hard-linked, so this collection does not duplicate
their video bytes on Firebird. A smaller ZIP contains every non-video member
for Dropbox access to PDFs, CSVs, methods, and provenance.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile


RELEASES = (
    (
        "original_11",
        "grouptrial_2024_pscp_v1_5_1_processor_0_8_1_release_20260924_2130utc",
        "GroupTrial_2024_PSC_v1.5.1_processor0.8.1_viewer_v3_outlinedPSC_11_reviews.zip",
        "portable_v151r081_view_v3_outline_v1",
        "b2b151c10f2dcde08f3353c776999fd3b5b9f6b78f99f4cf18b46c527fa20a64",
        11,
    ),
    (
        "additional_10",
        "grouptrial_2024_additional_psc_v1_5_1_processor_0_8_1_20260925_1337utc",
        "GroupTrial_additional_PSC_v1.5.1_processor0.8.1_10_reviews.zip",
        "portable_additional_v151r081_view_v3_outline_v1",
        "809f0481c4d98d6471a8b67a7d6bc0bc8f226412104f4bacbd7cdbe1a9a5a1c2",
        10,
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validated_release(base: Path, spec: tuple[str, str, str, str, str, int]) -> dict:
    label, directory, archive_name, portable_name, expected_sha, expected_count = spec
    root = base / directory
    archive = root / archive_name
    portable = root / portable_name
    if not archive.is_file() or not portable.is_dir():
        raise FileNotFoundError(f"Incomplete source release: {root}")
    if sha256(archive) != expected_sha:
        raise ValueError(f"Source ZIP checksum mismatch: {archive}")
    with zipfile.ZipFile(archive) as source:
        if source.testzip() is not None:
            raise ValueError(f"Corrupt source ZIP: {archive}")
        names = source.namelist()
        video_count = sum(name.endswith(".mp4") for name in names)
        pdf_count = sum(name.endswith(".pdf") for name in names)
        version_names = [name for name in names if name.endswith("VERSION_CONTROL.json")]
        if len(version_names) != 1:
            raise ValueError(f"Missing or ambiguous version record: {archive}")
        version = json.loads(source.read(version_names[0]))
        required = {
            "psc_model_version": "1.5.1",
            "group_processor_version": "0.8.1-group",
            "review_view_version": "raw-psc-compare-v3",
            "pdf_track_style_version": "outlined-psc-v1",
            "qc_status": "UNREVIEWED",
        }
        for field, expected in required.items():
            if version.get(field) != expected:
                raise ValueError(f"{label}: {field}={version.get(field)!r}")
        if video_count != expected_count or pdf_count != 2 * expected_count:
            raise ValueError(f"Unexpected review count in {archive}")
    return {
        "label": label,
        "source_root": str(root),
        "source_zip": str(archive),
        "source_zip_bytes": archive.stat().st_size,
        "source_zip_sha256": expected_sha,
        "portable_directory": str(portable),
        "reviews": expected_count,
        "videos": video_count,
        "pdfs": pdf_count,
        "version": required,
    }


def build(base: Path, destination: Path) -> dict:
    release_rows = [validated_release(base, spec) for spec in RELEASES]
    if destination.exists():
        raise FileExistsError(f"Collection already exists: {destination}")
    destination.mkdir(parents=True)
    (destination / "archives").mkdir()
    (destination / "runs").mkdir()
    try:
        for row in release_rows:
            label = row["label"]
            source_zip = Path(row["source_zip"])
            archive_link = destination / "archives" / source_zip.name
            os.link(source_zip, archive_link)
            if sha256(archive_link) != row["source_zip_sha256"]:
                raise ValueError(f"Collection archive hash changed: {archive_link}")
            (destination / "runs" / label).symlink_to(row["portable_directory"], target_is_directory=True)

        readme = (
            "# GroupTrial 2024: PSC 1.5.1 complete collection\n\n"
            "This collection contains the 11 original and 10 additional GroupTrial reviews "
            "(21 total). All outputs are computational and UNREVIEWED for biological "
            "interpretation. PSC locations are inferred hypotheses.\n\n"
            "Both `archives/*.zip` files are complete, portable releases with videos, "
            "PDFs, CSVs, methods, and provenance. They are hard links to the verified "
            "source archives, so this folder uses no additional video storage on Firebird. "
            "The `runs/` entries are browse-only symlinks to the source release folders. "
            "For transfer off Firebird, download the ZIPs.\n\n"
            "`GroupTrial_2024_PSC_v1.5.1_reports_tables_21.zip` contains all non-MP4 "
            "members of both releases. Its HTML viewers need the matching MP4s from the "
            "complete archives to play video. It is intended as a smaller Dropbox copy "
            "of the tables, PDFs, methods, and provenance.\n\n"
            "The withdrawn viewer-v2 ZIP is deliberately excluded. Source TOMLs, "
            "IDtracker tracking, and original release folders were not changed.\n"
        )
        (destination / "README.md").write_text(readme)

        reports_zip = destination / "GroupTrial_2024_PSC_v1.5.1_reports_tables_21.zip"
        with zipfile.ZipFile(reports_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as target:
            target.writestr("COLLECTION_README.md", readme)
            for row in release_rows:
                with zipfile.ZipFile(row["source_zip"]) as source:
                    for info in source.infolist():
                        if info.is_dir() or info.filename.lower().endswith(".mp4"):
                            continue
                        target.writestr(f"{row['label']}/{info.filename}", source.read(info))
        with zipfile.ZipFile(reports_zip) as target:
            if target.testzip() is not None:
                raise ValueError("Reports-and-tables ZIP failed integrity test")
            reports_count = len(target.namelist())

        manifest = {
            "schema": "grouptrial-2024-collection-v1",
            "psc_model_version": "1.5.1",
            "group_processor_version": "0.8.1-group",
            "review_view_version": "raw-psc-compare-v3",
            "pdf_track_style_version": "outlined-psc-v1",
            "qc_status": "UNREVIEWED",
            "review_count": 21,
            "source_tomls_untouched": True,
            "releases": release_rows,
            "reports_tables_zip": str(reports_zip),
            "reports_tables_zip_bytes": reports_zip.stat().st_size,
            "reports_tables_zip_sha256": sha256(reports_zip),
            "reports_tables_member_count": reports_count,
            "withdrawn_viewer_v2_excluded": True,
        }
        (destination / "COLLECTION_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest
    except Exception:
        # Preserve any partial collection for forensic inspection; the source
        # releases remain intact and the caller receives the error.
        raise


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: grouptrial_collection.py PIPELINE_BASE DESTINATION")
    print(json.dumps(build(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
