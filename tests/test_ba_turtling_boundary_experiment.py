import unittest
import numpy as np
from ba_turtling_boundary_experiment import refine_boundaries,Rules
class BoundaryTests(unittest.TestCase):
 def fixture(self):
  a=np.zeros((800,2));old=np.zeros(800,bool);old[400:650]=True;e=np.ones(800,bool);return a,old,e
 def test_bounded_lookback(self):
  a,b,e=self.fixture();r=refine_boundaries(a,b,e,1000);m=r['candidate_mask'];self.assertFalse(m[99]);self.assertTrue(m[100]);self.assertEqual(r['adjustments'][0]['first_global_frame'],1100)
 def test_recovery_not_backfilled(self):
  a,b,e=self.fixture();e[:250]=False;m=refine_boundaries(a,b,e)['candidate_mask'];self.assertFalse(m[249]);self.assertTrue(m[250])
 def test_missing_not_backfilled(self):
  a,b,e=self.fixture();a[320]=np.nan;m=refine_boundaries(a,b,e)['candidate_mask'];self.assertFalse(m[320]);self.assertTrue(m[321])
 def test_jump_stops_backsearch(self):
  a,b,e=self.fixture();a[:350,0]=25;m=refine_boundaries(a,b,e)['candidate_mask'];self.assertFalse(m[349]);self.assertTrue(m[350])
 def test_fixed_reference_stops_drift(self):
  a,b,e=self.fixture();a[:400,0]=np.arange(400,0,-1);m=refine_boundaries(a,b,e)['candidate_mask'];self.assertFalse(m[364]);self.assertTrue(m[365])
 def test_stationary_tail_not_trimmed(self):
  a,b,e=self.fixture();r=refine_boundaries(a,b,e);self.assertTrue(all(r['candidate_mask'][400:650]));self.assertFalse(any(x['kind']=='directed_departure_trim' for x in r['adjustments']))
 def test_sustained_directional_exit_trimmed(self):
  a,b,e=self.fixture();a[600:,0]=np.arange(200)*2;r=refine_boundaries(a,b,e);trims=[x for x in r['adjustments'] if x['kind']=='directed_departure_trim'];self.assertEqual(len(trims),1);self.assertFalse(r['candidate_mask'][649])
 def test_rapid_reversals_not_walking(self):
  a,b,e=self.fixture();a[550:,0]=np.where(np.arange(250)%2,8,-8);r=refine_boundaries(a,b,e);self.assertTrue(all(r['candidate_mask'][550:650]))
 def test_missing_exit_window_not_walking(self):
  a,b,e=self.fixture();a[660:]=np.nan;r=refine_boundaries(a,b,e);self.assertFalse(any(x['kind']=='directed_departure_trim' for x in r['adjustments']))
 def test_no_anchor_no_event(self):
  a,b,e=self.fixture();b[:]=False;self.assertFalse(any(refine_boundaries(a,b,e)['candidate_mask']))
 def test_existing_segment_stops_extension(self):
  a,b,e=self.fixture();b[200:350]=True;r=refine_boundaries(a,b,e);x=[x for x in r['adjustments'] if x['kind']=='onset_extension'][-1];self.assertEqual(x['first_global_frame'],350)
 def test_immutable_input_and_bad_gate(self):
  a,b,e=self.fixture();z=a.copy();refine_boundaries(a,b,e);np.testing.assert_array_equal(a,z);e[400]=False
  with self.assertRaises(ValueError):refine_boundaries(a,b,e)
 def test_bad_parameters(self):
  a,b,e=self.fixture()
  for rules in [Rules(onset_lookback_frames=2.5),Rules(exit_efficiency=2),Rules(max_step_px=float('nan'))]:
   with self.assertRaises(ValueError):refine_boundaries(a,b,e,rules=rules)
if __name__=='__main__':unittest.main()
