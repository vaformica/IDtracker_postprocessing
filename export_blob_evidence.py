#!/usr/bin/env python3
"""Export IDtracker blob detections for persistent-group post-processing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export(session, output=None) -> Path:
    # Import inside the function so the repository remains inspectable and
    # testable outside the IDtracker environment.
    from idtrackerai import ListOfBlobs

    session = Path(session)
    source = session / "preprocessing" / "list_of_blobs.pickle"
    if not source.is_file():
        raise FileNotFoundError("Persistent contact groups require preprocessing/list_of_blobs.pickle")
    destination = Path(output) if output else session / "blob_evidence.json"
    if destination.exists():
        raise FileExistsError(f"Refusing existing blob evidence: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    blobs = ListOfBlobs.load(source)
    frames = {
        str(frame): [
            dict(
                centroid=list(map(float, blob.centroid)),
                identities=[int(identity) if identity is not None else None for identity in blob.final_identities],
                crossing=bool(blob.is_a_crossing),
            )
            for blob in frame_blobs
        ]
        for frame, frame_blobs in enumerate(blobs.blobs_in_video)
    }
    payload = dict(
        schema="idtracker-blob-evidence-v1",
        source=str(source.resolve()),
        source_sha256=sha256(source),
        frames=frames,
    )
    partial = destination.with_name(destination.name + f".partial.{os.getpid()}")
    try:
        with partial.open("x") as stream:
            json.dump(payload, stream, separators=(",", ":"))
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session")
    parser.add_argument("--output")
    args = parser.parse_args()
    print(export(args.session, args.output))


if __name__ == "__main__":
    main()
