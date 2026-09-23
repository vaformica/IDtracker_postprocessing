import unittest
import numpy as np
from persistent_groups import persistent_groups

def blob(x,ids=()):return dict(centroid=[x,0],identities=list(ids))
class PersistentTests(unittest.TestCase):
 def test_pile_survives_unidentified_blob_and_missing_frame(self):
  r=np.full((7,2,2),np.nan);r[0]=[[0,0],[10,0]];r[4,0]=[14,0]
  b={'0':[blob(5)],'1':[blob(7)],'2':[blob(9)],'3':[],'4':[blob(14)],'5':[blob(16)],'6':[blob(18)]}
  g=persistent_groups(r,b)
  self.assertFalse(g['masks'][0,1][0])
  self.assertEqual(list(g['source'][0]),['ASSIGNED','ASSIGNED'])
  self.assertTrue(np.isnan(g['xy'][3]).all())
  for t in [1,2,4,5,6]:self.assertTrue(g['masks'][0,1][t])
  self.assertEqual(g['group_ids'][2,1],g['group_ids'][3,1])
  self.assertTrue(g['unresolved_masks'][0,1][3])
 def test_moving_pile_reacquires_after_short_total_detection_gap(self):
  r=np.full((4,2,2),np.nan);r[0]=[[0,0],[4,0]];r[3,0]=[80,0]
  b={'0':[blob(2)],'1':[],'2':[],'3':[blob(80)]}
  g=persistent_groups(r,b)
  self.assertTrue(np.isnan(g['xy'][1:3]).all())
  self.assertTrue(g['unresolved_masks'][0,1][1:3].all())
  self.assertEqual(list(g['xy'][3,:,0]),[80,80])
  self.assertTrue(g['masks'][0,1][3])
  strict=persistent_groups(r,b,gap_radius_cap=65.)
  self.assertTrue(np.isnan(strict['xy'][3]).all())
  self.assertTrue(strict['unresolved_masks'][0,1][3])
 def test_distant_identity_is_not_stolen(self):
  r=np.array([[[0,0]],[[500,0]],[[500,0]]],float)
  g=persistent_groups(r,{'0':[blob(0)],'1':[blob(500)],'2':[blob(500)]})
  self.assertTrue(np.isnan(g['xy'][1:]).all())
 def test_split_requires_consistent_separate_detections(self):
  r=np.array([[[0,0],[1,0]],[[0,0],[80,0]],[[0,0],[80,0]],[[0,0],[80,0]]],float)
  b={'0':[blob(0)],'1':[blob(0),blob(80)],'2':[blob(0),blob(80)],'3':[blob(0),blob(80)]}
  g=persistent_groups(r,b)
  self.assertFalse(g['masks'][0,1][3]);self.assertTrue(any(e['kind']=='SPLIT_CONFIRMED' for e in g['events']))
class PendingSplitTests(unittest.TestCase):
 def test_departing_blob_can_move_during_confirmation(self):
  r=np.array([[[0,0],[1,0]],[[0,0],[80,0]],[[0,0],[150,0]],[[0,0],[220,0]]],float)
  b={str(t):[blob(0)] if t==0 else [blob(0),blob(r[t,1,0])] for t in range(4)}
  g=persistent_groups(r,b)
  self.assertEqual(g['source'][3,1],'ASSIGNED')
  self.assertEqual(g['xy'][3,1,0],220)
  self.assertFalse(g['masks'][0,1][3])
if __name__=='__main__':unittest.main()
