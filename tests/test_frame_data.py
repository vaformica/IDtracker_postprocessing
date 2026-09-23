import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from frame_data import aggregate, write_frame_data


class FrameDataTests(unittest.TestCase):
    def test_two_animals_one_fungus_uses_dynamic_columns_and_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'frame_data.csv'
            xy = np.array([[[5., 5.], [6., 5.]], [[15., 5.], [16., 5.]]])
            masks = {(0,1): np.array([True, False])}
            result = dict(xy=xy.copy(), group=dict(xy=xy, source=np.full((2,2),'ASSIGNED'),
                inferred=np.zeros((2,2),bool), group_ids=np.array([[0,1],[0,1]]),
                ambiguous=np.zeros((2,2),bool), masks={(0,1):np.zeros(2,bool)}),
                masks=masks, metadata=dict(settings=dict(start=10),
                reconstruction=dict(max_speed_px_per_frame=100), rois=[
                    [[0,0],[100,0],[100,100],[0,100]],
                    [[10,0],[20,0],[20,10],[10,10]]]))
            write_frame_data(result, output)
            with output.open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 4)
            self.assertIn('fungus_1', rows[0])
            self.assertNotIn('fungus_2', rows[0])
            beetles, pairs = aggregate(output, 10, 11)
            self.assertEqual(len(beetles), 2)
            self.assertEqual(len(pairs), 1)
            self.assertEqual(beetles[0]['fungus_1_frames'], 1)
            self.assertEqual(pairs[0]['observed_proximity_frames'], 1)
            self.assertEqual(pairs[0]['unresolved_contact_frames'], 0)

    def test_locationless_pile_is_preserved_as_unresolved_not_pscp(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'frame_data.csv'
            xy=np.array([[[5.,5.],[5.,5.]],[[np.nan,np.nan],[np.nan,np.nan]],[[20.,5.],[20.,5.]]])
            raw=xy.copy()
            result=dict(xy=raw,group=dict(xy=xy,source=np.array([
                ['ASSIGNED','PSCP_BLOB'],['MISSING','MISSING'],['ASSIGNED','PSCP_BLOB']]),
                inferred=np.array([[0,1],[0,0],[0,1]],bool),group_ids=np.zeros((3,2),int),
                ambiguous=np.zeros((3,2),bool),masks={(0,1):np.array([1,0,1],bool)},
                unresolved_masks={(0,1):np.array([0,1,0],bool)}),
                masks={(0,1):np.zeros(3,bool)},metadata=dict(settings=dict(start=20),
                reconstruction=dict(max_speed_px_per_frame=100),rois=[
                    [[0,0],[100,0],[100,100],[0,100]],[[0,0],[30,0],[30,30],[0,30]]]))
            write_frame_data(result,output)
            with output.open(newline='') as stream:rows=list(csv.DictReader(stream))
            missing=[r for r in rows if r['global_frame']=='21']
            self.assertEqual([r['unresolved_contact_partners'] for r in missing],['1','0'])
            self.assertTrue(all(r['x']=='' and r['pscp_partners']=='' for r in missing))
            _,pairs=aggregate(output,20,22)
            self.assertEqual((pairs[0]['unresolved_contact_frames'],pairs[0]['pscp_frames']),(1,2))

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
