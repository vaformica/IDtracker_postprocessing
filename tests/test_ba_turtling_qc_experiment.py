import unittest
import numpy as np
from ba_turtling_qc_experiment import warnings
class TestBAQC(unittest.TestCase):
 def setUp(self):
  self.xy=np.random.default_rng(71).normal(0,2,(1000,2));self.eligible=np.ones(1000,bool)
 def test_local_irregular_motion_is_only_warning(self):
  r=warnings(self.xy,self.eligible,100);self.assertTrue(any(r['warning_mask']));self.assertIsNone(r['confirmed_turtling_seconds']);self.assertEqual(r['status'],'UNREVIEWED_QC_ONLY')
 def test_gap_breaks_persistence(self):
  self.xy[500]=np.nan;r=warnings(self.xy,self.eligible,100);self.assertFalse(any(r['warning_mask']));self.assertEqual(r['tracking_unknown'],[[600,600]])
 def test_recovery_breaks_persistence(self):
  self.eligible[500]=False;self.assertFalse(any(warnings(self.xy,self.eligible)['warning_mask']))
 def test_quiet_alone_not_irregular_motion(self):
  self.assertFalse(any(warnings(np.zeros((1000,2)),self.eligible)['warning_mask']))
