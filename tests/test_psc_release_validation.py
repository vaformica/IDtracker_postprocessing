import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from psc_release_validation import validate_bundle


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def bundle(self, positions, sources, ambiguous, inferred=None, conflict=None):
        path = self.root / 'canonical_states.npz'
        np.savez_compressed(path, xy=positions, source=sources, ambiguous=ambiguous,
                            inferred=np.zeros_like(ambiguous) if inferred is None else inferred,
                            identity_conflict=np.zeros_like(ambiguous) if conflict is None else conflict)
        manifest = dict(persistent_model_version='1.5.0', script_version='0.8.1-group',
                        qc_status='UNREVIEWED',
                        persistent_group_settings={'max_step_px_per_frame': 100},
                        output_sha256={'canonical_states.npz': hashlib.sha256(path.read_bytes()).hexdigest()})
        (self.root / 'manifest.json').write_text(json.dumps(manifest))

    def test_allows_unknown_split_and_bounded_gap_return(self):
        xy = np.array([[[0, 0]], [[np.nan, np.nan]], [[180, 0]]], float)
        source = np.array([['ASSIGNED'], ['UNRESOLVED_SPLIT'], ['ASSIGNED']])
        self.bundle(xy, source, np.array([[False], [True], [False]]))
        result = validate_bundle(self.root, '1.5.0', '0.8.1-group')
        self.assertEqual(result['unresolved_animal_frames'], 1)
        self.assertEqual(result['peak_speed_px_per_elapsed_frame'], 90)

    def test_rejects_impossible_transition(self):
        xy = np.array([[[0, 0]], [[500, 0]]], float)
        self.bundle(xy, np.array([['PSCP_BLOB'], ['PSCP_BLOB']]), np.zeros((2, 1), bool))
        with self.assertRaisesRegex(ValueError, 'Impossible PSC movement'):
            validate_bundle(self.root, '1.5.0', '0.8.1-group')

    def test_rejects_unflagged_unknown_split(self):
        xy = np.array([[[np.nan, np.nan]]], float)
        self.bundle(xy, np.array([['UNRESOLVED_SPLIT']]), np.array([[False]]))
        with self.assertRaisesRegex(ValueError, 'ambiguity flag'):
            validate_bundle(self.root, '1.5.0', '0.8.1-group')

    def test_backtraced_blob_must_remain_inferred_and_ambiguous(self):
        xy = np.array([[[0, 0]], [[5, 0]]], float)
        source = np.array([['ASSIGNED'], ['RETRO_REID_BLOB']])
        self.bundle(xy, source, np.array([[False], [True]]),
                    inferred=np.array([[False], [True]]))
        self.assertEqual(validate_bundle(self.root, '1.5.0', '0.8.1-group')
                         ['retrospective_reidentification_frames'], 1)
        self.bundle(xy, source, np.array([[False], [False]]),
                    inferred=np.array([[False], [True]]))
        with self.assertRaisesRegex(ValueError, 'Retrospective blob'):
            validate_bundle(self.root, '1.5.0', '0.8.1-group')

    def test_ownership_conflict_requires_unknown_location_and_flags(self):
        xy = np.array([[[np.nan, np.nan]]], float)
        source = np.array([['RAW_PSC_CONFLICT']])
        self.bundle(xy, source, np.array([[True]]), conflict=np.array([[True]]))
        self.assertEqual(validate_bundle(self.root, '1.5.0', '0.8.1-group')
                         ['unresolved_raw_psc_conflict_frames'], 1)
        self.bundle(xy, source, np.array([[True]]))
        with self.assertRaisesRegex(ValueError, 'ownership conflict'):
            validate_bundle(self.root, '1.5.0', '0.8.1-group')
