import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from frame_data import aggregate, write_frame_data


class FrameDataTests(unittest.TestCase):
    def test_rewindow_preserves_pile_credit_and_excludes_incoming_step(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'frame_data.csv'
            xy = np.zeros((3, 6, 2), dtype=float)
            for animal in range(6):
                xy[:, animal] = [100+animal*100, 100]
            xy[:, 0, 0] = [5, 15, 27]
            xy[:, 1, 0] = [5, 15, 27]
            raw = xy.copy()
            raw[1:, 1] = np.nan
            inferred = np.zeros((3, 6), dtype=bool)
            inferred[1:, 1] = True
            source = np.full((3, 6), 'ASSIGNED', dtype='<U20')
            source[1:, 1] = 'PSCP_BLOB'
            masks = {(a,b): np.zeros(3, dtype=bool) for a in range(6) for b in range(a+1,6)}
            masks[2,3][:2] = True
            pscp = {pair: mask.copy() for pair,mask in masks.items()}
            pscp[2,3][:] = False
            pscp[0,1][1:] = True
            result = dict(xy=raw, group=dict(xy=xy, source=source, inferred=inferred,
                group_ids=np.zeros((3,6),dtype=int), ambiguous=np.zeros((3,6),dtype=bool), masks=pscp),
                masks=masks, metadata=dict(settings=dict(start=50),
                reconstruction=dict(max_speed_px_per_frame=100), rois=[
                    [[0,0],[1000,0],[1000,1000],[0,1000]],
                    [[10,90],[19,90],[19,150],[10,150]],
                    [[21,90],[31,90],[31,150],[21,150]],
                    [[40,90],[50,90],[50,150],[40,150]]]))
            write_frame_data(result, output)
            with output.open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 18)
            pile = next(r for r in rows if r['global_frame']=='51' and r['animal_id']=='1')
            self.assertEqual((pile['raw_x'], pile['x'], pile['location_source']), ('', '15.0', 'PSCP_BLOB'))
            self.assertEqual((pile['fungus_1'], pile['pscp_partners']), ('1', '0'))
            beetles, pairs = aggregate(output, 51, 52)
            for animal in (0,1):
                row = beetles[animal]
                self.assertEqual((row['fungus_1_frames'],row['fungus_2_frames']), (1,1))
                self.assertEqual(row['any_fungus_percent_all_frames'],100)
                self.assertEqual(row['distance_px'],12)
                self.assertEqual(row['fungus_2_distance_px'],12)
            self.assertEqual(beetles[1]['inferred_location_frames'],2)
            self.assertEqual(next(p for p in pairs if (p['animal_a'],p['animal_b'])==(0,1))['pscp_frames'],2)
            self.assertEqual(next(p for p in pairs if (p['animal_a'],p['animal_b'])==(2,3))['observed_proximity_frames'],1)
            with self.assertRaisesRegex(ValueError, 'complete'):
                aggregate(output, 49, 52)


if __name__ == '__main__':
    unittest.main()
