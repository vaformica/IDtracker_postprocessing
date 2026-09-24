import csv
import json
import tempfile
import unittest
from pathlib import Path

from dyadic_quality import summary


class DyadicQualityTests(unittest.TestCase):
    def test_pile_and_retrospective_reidentification_have_separate_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            analysis = root / 'analysis'
            session = root / 'session'
            analysis.mkdir()
            session.mkdir()
            (analysis / 'manifest.json').write_text(json.dumps({
                'roi_order': ['arena', 'fungus_1'],
                'persistent_model_version': '1.5.0',
                'script_version': '0.8.1-group',
            }))
            (session / 'session.json').write_text('{}')
            rows = [
                dict(global_frame=0, animal_id=0, raw_x='', raw_y='', x=1, y=1,
                     location_source='PSCP_BLOB', pscp_partners='1',
                     unresolved_contact_partners='', identity_conflict=0),
                dict(global_frame=1, animal_id=0, raw_x='', raw_y='', x=2, y=2,
                     location_source='RETRO_REID_BLOB', pscp_partners='',
                     unresolved_contact_partners='', identity_conflict=0),
                dict(global_frame=2, animal_id=0, raw_x=3, raw_y=3, x='', y='',
                     location_source='RAW_PSC_CONFLICT', pscp_partners='',
                     unresolved_contact_partners='', identity_conflict=1),
            ]
            for row in rows:
                row.update(raw_fungus_1=0, fungus_1=0,
                           raw_step_distance_px='', step_distance_px='',
                           raw_step_midpoint_fungus_1=0, step_midpoint_fungus_1=0)
            with (analysis / 'frame_data.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            animal = summary(analysis, session, 'source.toml', 'sha')['animals'][0]
            self.assertEqual(animal['screened_without_pscp_missing_frames'], 3)
            self.assertEqual(animal['after_pscp_missing_frames'], 1)
            self.assertEqual(animal['raw_missing_frames_recovered_by_pscp'], 1)
            self.assertEqual(animal['raw_missing_frames_recovered_by_reidentification'], 1)
            self.assertEqual(animal['retrospective_reidentification_frames'], 1)
            self.assertEqual(animal['raw_psc_identity_conflict_frames'], 1)
            self.assertEqual(animal['unresolved_raw_psc_conflict_frames'], 1)
