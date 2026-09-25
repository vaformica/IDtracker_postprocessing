#!/usr/bin/env python3
"""Render a new outlined-PSC PDF from an existing, versioned analysis bundle.

The original analysis is read-only. Recompute from its hashed inputs, verify
that every raw and canonical state matches the published bundle, then write
only a PDF and its provenance sidecar in a new output directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from persistent_groups import MODEL_VERSION
from six_beetle_processor import (PDF_TRACK_STYLE_VERSION, SCRIPT_VERSION,
                                  analyze_six, sha256, write_pdf)


def render(analysis: Path, output: Path) -> Path:
    analysis = analysis.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest_path = analysis / 'manifest.json'
    meta = json.loads(manifest_path.read_text())
    if (meta.get('script_version') != SCRIPT_VERSION or
            meta.get('persistent_model_version') != MODEL_VERSION or
            meta.get('qc_status') != 'UNREVIEWED'):
        raise ValueError('Source bundle has the wrong processor, PSC, or review version')
    state_path = analysis / 'canonical_states.npz'
    if sha256(state_path) != meta['output_sha256']['canonical_states.npz']:
        raise ValueError('Published canonical states do not match their manifest')
    for name, expected in meta.get('input_sha256', {}).items():
        if sha256(Path(name)) != expected:
            raise ValueError(f'Analysis input changed: {name}')
    blob = Path(meta['blob_evidence_file'])
    if sha256(blob) != meta['blob_evidence_sha256']:
        raise ValueError('Detection evidence changed after the original analysis')

    group = meta['persistent_group_settings']
    settings = meta['settings']
    result = analyze_six(
        trajectory=meta['trajectory_file'], session=meta['session_folder'],
        blob_evidence=blob, **settings,
        reconstruction_speed_px=group['max_step_px_per_frame'],
        split_confirmation_frames=group['split_confirmation_frames'],
        gap_speed_px=group['gap_speed_px_per_frame'],
        gap_radius_cap_px=group['gap_radius_cap_px'],
        max_reacquire_gap_frames=group['max_reacquire_gap_frames'],
        distant_confirmation_frames=group['distant_confirmation_frames'],
    )
    with np.load(state_path, allow_pickle=False) as published:
        for key, actual in (('raw', result['xy']), ('xy', result['group']['xy']),
                            ('inferred', result['group']['inferred']),
                            ('group_ids', result['group']['group_ids']),
                            ('source', result['group']['source']),
                            ('ambiguous', result['group']['ambiguous']),
                            ('identity_conflict', result['group']['identity_conflict'])):
            if not np.array_equal(published[key], actual, equal_nan=actual.dtype.kind in 'fc'):
                raise ValueError(f'Recomputed {key} differs from the published PSC analysis')
    result['metadata']['frames_per_second'] = meta.get('frames_per_second')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.outlined-psc-pdf-', dir=output.parent))
    try:
        pdf_name = Path(meta['pdf_filename']).stem + '__PSC_paths_outlined.pdf'
        pdf_path = staging / pdf_name
        write_pdf(result, pdf_path, meta['video'], meta['cell_label'])
        sidecar = dict(
            schema='outlined-psc-pdf-v1',
            created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            source_analysis=str(analysis),
            source_manifest_sha256=sha256(manifest_path),
            source_canonical_sha256=sha256(state_path),
            processor_version=SCRIPT_VERSION,
            psc_model_version=MODEL_VERSION,
            pdf_track_style_version=PDF_TRACK_STYLE_VERSION,
            review_status='UNREVIEWED',
            raw_and_psc_states_matched=True,
            source_analysis_untouched=True,
            pdf_filename=pdf_name,
            pdf_sha256=sha256(pdf_path),
            renderer_sha256=sha256(Path(__file__)),
            processor_code_sha256=sha256(Path(__file__).with_name('six_beetle_processor.py')),
        )
        (staging / 'render_manifest.json').write_text(json.dumps(sidecar, indent=2) + '\n')
        os.rename(staging, output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output / pdf_name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(render(args.analysis, args.output), flush=True)


if __name__ == '__main__':
    main()
