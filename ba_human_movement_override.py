"""Apply an explicit dataset-bound BA review override to a COPY of movement data.

Call after importing the viewer JSON. Never use usable_skim alone as authority.
The strict coordinates are retained; no endpoint restoration or gap bridging.
"""
import copy
import numpy as np

VERSION = '1.1.0'

def apply_override(strict_track, automatic_movement, export, dataset_hash, run_id):
    if export.get('schema') != 'ba-combined-qc-v1' or export.get('dataset_sha256') != dataset_hash:
        raise ValueError('Wrong score schema or dataset')
    rows = [d for d in export.get('decisions', []) if d.get('run_id') == run_id]
    if len(rows) != 1:
        raise ValueError('Require one saved decision for this run')
    decision = rows[0]
    result = np.array(automatic_movement, dtype=float, copy=True)
    if decision.get('movement_override') is not True:
        return result, {'applied': False, 'version': VERSION}
    if (decision.get('status') != 'usable_skim' or decision.get('rerun_idtracker')
        or not isinstance(decision.get('errors'), list)
        or not isinstance(decision.get('reviewer'), str) or not decision['reviewer'].strip()
        or not decision.get('at')
        or decision.get('scope') not in ('trace_skim', 'trace_and_excerpt', 'trace_and_full_video')
        or decision.get('effective_movement_status') != 'HUMAN_OVERRIDE_USE_STRICT_TRACK'
        or decision.get('review_does_not_clear_analysis_hold') is not False):
        raise ValueError('Incomplete or conflicting human override')
    track = np.asarray(strict_track, dtype=float)
    if track.ndim != 2 or track.shape[1] != 2 or result.shape != (len(track)-1,):
        raise ValueError('Invalid strict track or movement shape')
    result = np.linalg.norm(np.diff(track, axis=0), axis=1)
    # Finite adjacent strict positions only; never bridge missing/excluded endpoints.
    result[~np.isfinite(result)] = np.nan
    return result, {'applied': True, 'version': VERSION,
                    'dataset_sha256': dataset_hash, 'run_id': run_id,
                    'status': 'HUMAN_OVERRIDE_USE_STRICT_TRACK',
                    'decision': copy.deepcopy(decision),
                    'analysis_approved': True,
                    'possible_flags': copy.deepcopy(decision.get('errors', [])),
                    'finite_movement_steps': int(np.isfinite(result).sum())}
