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
  r=np.full((17,2,2),np.nan)
  r[0]=[[0,0],[2,0]]
  for t in range(4,17):
   r[t,0]=[220+t-4,0];r[t,1]=[20+t-4,0]
  b={str(t):[blob(1+t)] for t in range(4)}
  for t in range(4,17):b[str(t)]=[blob(r[t,1,0],ids=(2,)),blob(r[t,0,0],ids=(1,))]
  g=persistent_groups(r,b)
  self.assertTrue(np.isnan(g['xy'][11:13,0]).all())
  self.assertTrue(np.all(g['xy'][4:11,0]<100))
  self.assertEqual(g['xy'][13,0,0],229)
  self.assertEqual(g['xy'][13,1,0],29)
  self.assertTrue(any(e['kind']=='DISTANT_RAW_REACQUIRED' for e in g['events']))
 def test_one_frame_false_raw_identity_does_not_end_pile(self):
  r=np.full((5,2,2),np.nan);r[0]=[[0,0],[2,0]];r[2,0]=[220,0]
  b={'0':[blob(1)],'1':[blob(3)],'2':[blob(5),blob(220)],'3':[blob(7)],'4':[blob(9)]}
  g=persistent_groups(r,b)
  self.assertEqual(g['source'][2,0],'PSCP_BLOB')
  self.assertEqual(g['xy'][2,0,0],5)
  self.assertTrue(g['masks'][0,1][3:5].all())
 def test_far_false_id_on_another_beetle_does_not_steal_pile_member(self):
  r=np.full((6,3,2),np.nan)
  r[0]=[[800,0],[0,0],[1,0]]
  r[1:,:,1]=0
  for t in range(1,6):
   r[t,1]=[800+t,0];r[t,2]=[t,0]
  b={'0':[blob(800,ids=(1,)),blob(0,ids=(2,3))]}
  for t in range(1,6):b[str(t)]=[blob(800+t,ids=(2,)),blob(t,ids=(3,))]
  g=persistent_groups(r,b)
  self.assertTrue((g['group_ids'][1:,1]==g['group_ids'][1:,2]).all())
  self.assertTrue(np.all(g['xy'][1:,1,0]<100))
  self.assertTrue(np.all(np.linalg.norm(np.diff(g['xy'][:,1],axis=0),axis=1)<=100))
 def test_short_false_id_burst_does_not_move_hidden_member(self):
  r=np.full((9,2,2),np.nan);r[0]=[[0,0],[1,0]]
  b={'0':[blob(0,ids=(1,2))]}
  for t in range(1,9):
   b[str(t)]=[blob(t,ids=(2,))]
   if 3<=t<=5:
    r[t,0]=[250+t,0];b[str(t)].append(blob(250+t,ids=(1,)))
  g=persistent_groups(r,b)
  self.assertTrue((g['group_ids'][:,0]==g['group_ids'][:,1]).all())
  self.assertTrue(np.all(g['xy'][:,0,0]<100))
 def test_unresolved_multiway_member_rejoins_only_former_partner(self):
  r=np.full((9,4,2),np.nan)
  r[0]=[[0,0],[1,0],[2,0],[800,0]]
  b={'0':[blob(1,ids=(1,2,3)),blob(800,ids=(4,))]}
  for t in range(1,9):
   r[t,0]=[t,0];r[t,2]=[60+t,0];r[t,3]=[800+t,0]
   b[str(t)]=[blob(t,ids=(1,)),blob(60+t,ids=(3,)),blob(800+t,ids=(4,))]
   if t>=4:
    r[t,1]=[t,0];b[str(t)][0]['identities'].append(2)
  g=persistent_groups(r,b)
  self.assertTrue(np.isnan(g['xy'][3,1]).all())
  self.assertEqual(g['source'][3,1],'UNRESOLVED_SPLIT')
  self.assertTrue(g['ambiguous'][3,1])
  self.assertEqual(g['group_ids'][8,0],g['group_ids'][8,1])
  self.assertNotEqual(g['group_ids'][8,1],g['group_ids'][8,3])
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
 def test_confirmed_raw_id_backtraces_unique_unlabeled_departure(self):
  r=np.full((25,2,2),np.nan)
  r[0]=[[0,0],[1,0]]
  for t in range(1,25):r[t,1]=[0,0]
  for t in range(14,25):r[t,0]=[20+10*(t-4),0]
  b={'0':[blob(0,ids=(1,2))]}
  for t in range(1,25):
   b[str(t)]=[blob(0,ids=(2,))]
   if t>=4:b[str(t)].append(blob(20+10*(t-4),ids=(1,) if t>=14 else (None,)))
  g=persistent_groups(r,b)
  self.assertTrue((g['source'][1:4,0]=='DEPARTURE_UNCERTAIN').all())
  self.assertTrue(np.isnan(g['xy'][1:4,0]).all())
  self.assertEqual(g['source'][4,0],'RETRO_REID_BLOB')
  self.assertTrue(g['ambiguous'][4,0])
  self.assertEqual(g['xy'][10,0,0],80)
  self.assertFalse(g['masks'][0,1][10])
  self.assertEqual(g['source'][14,0],'ASSIGNED')
  self.assertTrue(g['identity_conflict'][14,0])
  self.assertTrue(any(e['kind']=='RETRO_REID_BACKTRACE' and e['first_frame']==4
                      for e in g['events']))
 def test_sustained_raw_id_on_another_entity_is_review_conflict(self):
  r=np.full((16,3,2),np.nan)
  r[0]=[[0,0],[1,0],[300,0]]
  for t in range(1,16):
   r[t,0]=[300+t,0];r[t,1]=[0,0]
  b={'0':[blob(0,ids=(1,2)),blob(300,ids=(3,))]}
  for t in range(1,16):b[str(t)]=[blob(0,ids=(2,)),blob(300+t,ids=(1,))]
  g=persistent_groups(r,b)
  self.assertTrue(g['identity_conflict'][10,0])
  self.assertTrue(any(e['kind']=='RAW_ID_OWNERSHIP_CONFLICT' for e in g['events']))
  self.assertEqual(g['source'][14,0],'RAW_PSC_CONFLICT')
  self.assertTrue(np.isnan(g['xy'][14,0]).all())
  self.assertTrue(np.all(g['xy'][1:13,0,0]<100))
if __name__=='__main__':unittest.main()
