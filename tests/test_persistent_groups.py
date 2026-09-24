import unittest
import numpy as np
from persistent_groups import persistent_groups

def blob(x,ids=()):return dict(centroid=[x,0],identities=list(ids))
class PersistentTests(unittest.TestCase):
 def test_pile_survives_unidentified_blob_and_missing_frame(self):
  r=np.full((7,2,2),np.nan);r[0]=[[0,0],[10,0]];r[4,0]=[14,0]
  b={'0':[blob(5)],'1':[blob(7)],'2':[blob(9)],'3':[],'4':[blob(14)],'5':[blob(16)],'6':[blob(18)]}
  g=persistent_groups(r,b)
  self.assertTrue(g['masks'][0,1][0])
  self.assertEqual(sorted(g['source'][0]),['ASSIGNED','PSCP_BLOB'])
  self.assertTrue(np.isnan(g['xy'][3]).all())
  for t in [1,2,4,5,6]:self.assertTrue(g['masks'][0,1][t])
  self.assertEqual(g['group_ids'][2,1],g['group_ids'][3,1])
  self.assertTrue(g['unresolved_masks'][0,1][3])
 def test_two_idtracker_coordinates_on_one_blob_are_one_visible_plus_pscp(self):
  r=np.array([[[0,0],[10,0]],[[2,0],[8,0]],[[3,0],[7,0]]],float)
  b={str(t):[blob(6+t)] for t in range(3)}
  g=persistent_groups(r,b)
  self.assertTrue(g['masks'][0,1].all())
  self.assertTrue((g['inferred'].sum(axis=1)==1).all())
  self.assertTrue((g['source']=='ASSIGNED').sum(axis=1).tolist()==[1,1,1])
  self.assertTrue(np.isfinite(g['xy']).all())
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
 def test_far_reappearance_splits_after_confirmation_without_dragging_pile(self):
  r=np.full((7,2,2),np.nan)
  r[0]=[[0,0],[2,0]]
  r[4:,0]=[[220,0],[230,0],[240,0]]
  r[4:,1]=[[20,0],[22,0],[24,0]]
  b={str(t):[blob(10+t)] for t in range(4)}
  for t in range(4,7):b[str(t)]=[blob(r[t,1,0]),blob(r[t,0,0])]
  g=persistent_groups(r,b)
  self.assertTrue(g['unresolved_masks'][0,1][4:6].all())
  self.assertTrue(np.isnan(g['xy'][4:6]).all())
  self.assertEqual(g['xy'][6,0,0],240)
  self.assertEqual(g['xy'][6,1,0],24)
  self.assertFalse(g['masks'][0,1][6])
 def test_one_frame_false_raw_identity_does_not_end_pile(self):
  r=np.full((5,2,2),np.nan);r[0]=[[0,0],[2,0]];r[2,0]=[220,0]
  b={'0':[blob(1)],'1':[blob(3)],'2':[blob(5),blob(220)],'3':[blob(7)],'4':[blob(9)]}
  g=persistent_groups(r,b)
  self.assertTrue(g['ambiguous'][2,0])
  self.assertTrue(np.isnan(g['xy'][2,0]).all())
  self.assertTrue(g['masks'][0,1][3:5].all())
 def test_distant_three_id_blob_is_flagged_instead_of_teleporting(self):
  r=np.full((7,3,2),np.nan)
  r[0]=[[0,0],[2,0],[220,0]]
  for t in range(4,7):r[t]=[[20+t,0],[22+t,0],[24+t,0]]
  b={str(t):[blob(10+t),blob(220)] for t in range(4)}
  for t in range(4,7):b[str(t)]=[blob(22+t,ids=(1,2,3))]
  g=persistent_groups(r,b)
  self.assertTrue(g['ambiguous'][6,2])
  self.assertTrue(np.isnan(g['xy'][6,2]).all())
  self.assertFalse(g['masks'][0,2][6])
if __name__=='__main__':unittest.main()
