import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from psc_disagreement_audit import audit


class PSCDisagreementAuditTests(unittest.TestCase):
    def test_flags_distinct_raw_blob_and_split_three_identity_blob(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fields = ['global_frame', 'animal_id', 'raw_x', 'raw_y', 'x', 'y',
                      'location_source', 'group_id', 'pscp_partners']
            rows = [
                [0, 0, 100, 100, 0, 0, 'PSCP_BLOB', 1, '1'],
                [0, 1, 101, 100, 100, 100, 'ASSIGNED', 2, ''],
                [0, 2, 99, 100, 100, 100, 'ASSIGNED', 2, ''],
            ]
            with (root / 'frame_data.csv').open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(fields)
                writer.writerows(rows)
            (root / 'blobs.json').write_text(json.dumps({'frames': {'0': [
                {'centroid': [100, 100], 'identities': [1, 2, 3]},
                {'centroid': [0, 0], 'identities': []}]}}))
            np.save(root / 'trajectory.npy', {'id_probabilities':
                    np.ones((1, 3, 1))}, allow_pickle=True)
            result = audit(root / 'frame_data.csv', root / 'blobs.json',
                           root / 'trajectory.npy', root / 'report', 60)
            self.assertEqual(result['total_pscp_raw_conflict_frames'], 1)
            self.assertEqual(result['three_plus_identity_blob_conflict_frames'], 1)
            self.assertEqual(result['per_animal']['0']['longest_consecutive_conflict_frames'], 1)


if __name__ == '__main__':
    unittest.main()
