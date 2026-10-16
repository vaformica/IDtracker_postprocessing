import unittest
import numpy as np
from encounter_orientation_pilot import velocity, radial, events_for_pair, attribution

class EncounterPilotTests(unittest.TestCase):
 def test_velocity_units_and_edges(self):
  raw=np.zeros((90,2,2));raw[:,0,0]=np.arange(90)*2
  v=velocity(raw,np.ones((90,2),bool),30,13)
  np.testing.assert_allclose(v[6:-6,0,0],60)
  self.assertTrue(np.isnan(v[:6]).all());self.assertTrue(np.isnan(v[-6:]).all())
 def test_no_bridging_unsupported_or_jump(self):
  raw=np.zeros((90,2,2));ok=np.ones((90,2),bool);ok[30,0]=False
  raw[60:,1,0]=100
  v=velocity(raw,ok,30,13)
  self.assertTrue(np.isnan(v[24:37,0]).all())
  self.assertTrue(np.isnan(v[54:66,1]).all())
 def test_radial_sign_and_distance_derivative(self):
  raw=np.zeros((50,2,2));raw[:,1,0]=100
  v=np.zeros_like(raw);v[:,0,0]=10;v[:,1,0]=4
  dist,a,b=radial(raw,v,np.ones((50,2),bool),0,1)
  np.testing.assert_allclose(a,10);np.testing.assert_allclose(b,-4)
  np.testing.assert_allclose(a+b,6)
  self.assertEqual(attribution(a,b,0,30,'approach',30)['label'],'A')
 def test_departing_second_beetle(self):
  x=np.zeros(30);y=np.full(30,-15.)
  self.assertEqual(attribution(x,y,0,30,'departure',30)['label'],'B')
 def test_unknown_is_not_stationary(self):
  x=np.full(30,np.nan);y=np.zeros(30)
  self.assertIn('Unknown',attribution(x,y,0,30,'approach',30)['label'])
 def test_zero_distance_unknown_radial(self):
  _,a,b=radial(np.zeros((30,2,2)),np.zeros((30,2,2)),np.ones((30,2),bool),0,1)
  self.assertTrue(np.isnan(a).all());self.assertTrue(np.isnan(b).all())
 def test_global_inclusive_events_and_censoring(self):
  raw=np.zeros((120,2,2));raw[:,1,0]=100;raw[40:60,1,0]=50
  ok=np.ones((120,2),bool);vs={w:np.zeros_like(raw) for w in (7,13,25)}
  e=events_for_pair(raw,ok,vs,0,1,30,1000)[0]
  self.assertEqual((e['first_global_frame'],e['last_global_frame']),(1040,1059))
  raw[39,1]=np.nan;e=events_for_pair(raw,ok,vs,0,1,30,1000)[0]
  self.assertFalse(e['entry_observed']);self.assertIn('censored',e['estimates']['13']['approach']['label'])

if __name__=='__main__':unittest.main()
