"""Version and movement gates for publishing shared PSC analysis bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


def validate_bundle(analysis: Path, model: str, processor: str) -> dict:
    analysis = Path(analysis)
    manifest = json.loads((analysis / 'manifest.json').read_text())
    if (manifest.get('persistent_model_version') != model or
            manifest.get('script_version') != processor or
            manifest.get('qc_status') != 'UNREVIEWED'):
        raise ValueError(f'Wrong PSC version or review status: {analysis}')
    state_path = analysis / 'canonical_states.npz'
    expected_hash = manifest.get('output_sha256', {}).get(state_path.name)
    if not expected_hash or hashlib.sha256(state_path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError(f'Canonical state hash mismatch: {analysis}')
    with np.load(state_path, allow_pickle=False) as data:
        xy = data['xy']
        source = data['source']
        ambiguous = data['ambiguous']
        inferred = data['inferred']
        conflict = data['identity_conflict']
    if (xy.ndim != 3 or xy.shape[2] != 2 or
            any(field.shape != xy.shape[:2] for field in
                (source, ambiguous, inferred, conflict))):
        raise ValueError(f'Invalid canonical state shape: {analysis}')
    retrospective = source == 'RETRO_REID_BLOB'
    if np.any(~np.isfinite(xy[retrospective])) or np.any(~ambiguous[retrospective]) or np.any(~inferred[retrospective]):
        raise ValueError(f'Retrospective blob location lacks inference/ambiguity flag: {analysis}')
    ownership_conflict = source == 'RAW_PSC_CONFLICT'
    if (np.any(np.isfinite(xy[ownership_conflict])) or
            np.any(~ambiguous[ownership_conflict]) or
            np.any(~conflict[ownership_conflict])):
        raise ValueError(f'Raw/PSC ownership conflict lacks missing position or flags: {analysis}')
    uncertain_departure = source == 'DEPARTURE_UNCERTAIN'
    if (np.any(np.isfinite(xy[uncertain_departure])) or
            np.any(~ambiguous[uncertain_departure])):
        raise ValueError(f'Uncertain departure was scored with a position: {analysis}')
    unresolved = source == 'UNRESOLVED_SPLIT'
    if np.any(np.isfinite(xy[unresolved])) or np.any(~ambiguous[unresolved]):
        raise ValueError(f'Unresolved split has position or lacks ambiguity flag: {analysis}')
    limit = float(manifest['persistent_group_settings']['max_step_px_per_frame'])
    if not np.isfinite(limit) or limit <= 0:
        raise ValueError(f'Invalid movement limit: {analysis}')
    peak_rate = 0.0
    for animal in range(xy.shape[1]):
        known = np.flatnonzero(np.isfinite(xy[:, animal]).all(axis=1))
        if len(known) < 2:
            continue
        elapsed = np.diff(known)
        rate = np.linalg.norm(np.diff(xy[known, animal], axis=0), axis=1) / elapsed
        peak_rate = max(peak_rate, float(rate.max()))
        if np.any(rate > limit + 1e-6):
            raise ValueError(f'Impossible PSC movement for animal {animal}: {analysis}')
    return dict(frames=int(xy.shape[0]), animals=int(xy.shape[1]),
                unresolved_animal_frames=int(unresolved.sum()),
                retrospective_reidentification_frames=int(retrospective.sum()),
                unresolved_raw_psc_conflict_frames=int(ownership_conflict.sum()),
                uncertain_departure_frames=int(uncertain_departure.sum()),
                raw_psc_identity_conflict_frames=int(conflict.sum()),
                peak_speed_px_per_elapsed_frame=peak_rate)
