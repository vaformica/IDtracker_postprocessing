import unittest
import numpy as np
from close_encounter_pilot import episodes,boundary,build_events

class CloseEncounterTests(unittest.TestCase):
 def test_exit_hysteresis_and_backdate(self):
  d=np.array([70,49,51,55,49]+[70]*7,float)
  self.assertEqual(episodes(d,np.zeros(len(d),bool),50,30),[(1,5,True)])
 def test_missing_is_not_departure(self):
  d=np.array([70,49,np.nan,48,70,70],float)
  self.assertEqual(episodes(d,np.zeros(6,bool),50,30),[(1,2,False),(3,6,False)])
 def test_psc_bridges_missing_only_when_present(self):
  d=np.array([70,49,np.nan,48]+[70]*6,float);p=np.zeros(10,bool);p[2]=True
  self.assertEqual(episodes(d,p,50,30),[(1,4,True)])
 def test_entry_contributor_not_receding_partner(self):
  raw=np.zeros((50,2,2));raw[:,0,0]=np.arange(50);raw[:,1,0]=80
  r=boundary(raw,np.ones((50,2),bool),0,1,30,True,50,30)
  self.assertEqual(r['label'],'A')
  self.assertTrue(r['first_mover'].startswith('Unknown'))
 def test_departure_correct_sign(self):
  raw=np.zeros((50,2,2));raw[:,0,0]=-np.arange(50);raw[:,1,0]=40
  self.assertEqual(boundary(raw,np.ones((50,2),bool),0,1,10,False,50,30)['label'],'A')
 def test_unsupported_boundary_abstains(self):
  raw=np.zeros((50,2,2));raw[:,0,0]=np.arange(50);raw[:,1,0]=80
  s=np.ones((50,2),bool);s[29,0]=False
  self.assertEqual(boundary(raw,s,0,1,30,True,50,30)['label'],'Unknown')
 def test_far_movement_excluded(self):
  raw=np.zeros((50,2,2));raw[:,0,0]=np.arange(50);raw[:,1,0]=300
  self.assertEqual(boundary(raw,np.ones((50,2),bool),0,1,30,True,50,30)['label'],'Unknown')
 def test_visible_local_onset(self):
  raw=np.zeros((40,2,2));raw[:,1,0]=80;raw[15:,0,0]=np.arange(25)
  self.assertEqual(boundary(raw,np.ones((40,2),bool),0,1,30,True,50,30)['first_mover'],'A')
if __name__=='__main__':unittest.main()
