import unittest
import numpy as np
from proximity60_pilot import episodes,boundary,build_events
class Proximity60Tests(unittest.TestCase):
 def test_exact_sixty_entry_exit(self):
  d=np.array([61,60,59]+[61]*6,float)
  self.assertEqual(episodes(d,np.zeros(9,bool),60,30),[(1,3,True)])
 def test_unknown_not_departure(self):
  self.assertEqual(episodes(np.array([61,60,np.nan]),np.zeros(3,bool),60,30),[(1,2,False)])
 def test_both(self):
  raw=np.zeros((40,2,2));raw[:,0,0]=np.arange(40)*.5;raw[:,1,0]=100-np.arange(40)*.5
  self.assertEqual(boundary(raw,np.ones((40,2),bool),0,1,30,True,60,30)['label'],'Both')
 def test_psc_without_crossing_not_initiator(self):
  raw=np.zeros((50,2,2));raw[:,0,0]=np.arange(50)*.1;raw[:,1,0]=90
  p=np.zeros(50,bool);p[30:40]=True
  e=build_events(raw,np.ones((50,2),bool),{(0,1):p},30,100,np.array([40,40]))
  self.assertEqual(e[0]['approach']['label'],'Unknown')
 def test_overlap_boundary_unknown(self):
  raw=np.zeros((40,2,2));raw[:,1,0]=90-np.arange(40);s=np.ones((40,2),bool);s[29]=False
  self.assertEqual(boundary(raw,s,0,1,30,True,60,30)['label'],'Unknown')
if __name__=='__main__':unittest.main()
