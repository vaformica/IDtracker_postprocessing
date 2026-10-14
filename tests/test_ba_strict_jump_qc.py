import unittest
import numpy as np
from ba_strict_jump_qc import gate
class StrictJumpTests(unittest.TestCase):
 def test_threshold_and_no_invented_repair(self):
  a=np.array([[0.,0.],[100.,0.],[101.,0.],[0.,0.]])
  original=a.copy();t,m,q=gate(a,50)
  np.testing.assert_equal(a,original)
  self.assertEqual(q['jump_pairs'],[[50,51],[52,53]])
  self.assertTrue(np.isnan(t).all());self.assertTrue(np.isnan(m).all())
  self.assertEqual(q['boundaries'],'UNRESOLVED')
 def test_gap_never_supplies_movement(self):
  t,m,q=gate([[0,0],[1,0],[np.nan,np.nan],[500,0],[501,0]],10)
  np.testing.assert_equal(m,[1,np.nan,np.nan,1])
  self.assertFalse(q['human_run_review_required'])
 def test_whole_run_movement_blocked(self):
  t,m,q=gate([[0,0],[1,0],[200,0],[201,0],[202,0]],0)
  self.assertTrue(np.isnan(m).all())
  self.assertTrue(np.isfinite(t[-1]).all())
  self.assertEqual(q['uncertain_frames'],[1,2])
if __name__=='__main__':unittest.main()
