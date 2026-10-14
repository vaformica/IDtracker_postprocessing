import unittest
import numpy as np
from ba_human_movement_override import apply_override

class OverrideTests(unittest.TestCase):
 def setUp(self):
  self.track=np.array([[0,0],[1,0],[np.nan,np.nan],[500,0],[503,0]])
  self.original=np.full(4,np.nan)
  self.d=dict(run_id='r1',status='usable_skim',errors=[],reviewer='TEST',at='2026-10-13',scope='trace_skim',movement_override=True,effective_movement_status='HUMAN_OVERRIDE_USE_STRICT_TRACK',review_does_not_clear_analysis_hold=False)
  self.export=dict(schema='ba-combined-qc-v1',dataset_sha256='abc',decisions=[self.d])
 def test_override_no_bridging_or_original_mutation(self):
  m,receipt=apply_override(self.track,self.original,self.export,'abc','r1')
  np.testing.assert_equal(m,[1,np.nan,np.nan,3]);self.assertTrue(np.isnan(self.original).all());self.assertTrue(receipt['applied'])
 def test_approved_with_flags_keeps_movement_and_flags(self):
  self.d['errors']=['jumps','possible_turtling']
  m,r=apply_override(self.track,self.original,self.export,'abc','r1')
  np.testing.assert_equal(m,[1,np.nan,np.nan,3]);self.assertEqual(r['possible_flags'],self.d['errors']);self.assertTrue(r['analysis_approved'])
 def test_usable_alone_does_not_override(self):
  self.d.pop('movement_override');m,r=apply_override(self.track,self.original,self.export,'abc','r1')
  self.assertTrue(np.isnan(m).all());self.assertFalse(r['applied'])
 def test_conflicting_or_wrong_dataset_rejected(self):
  with self.assertRaises(ValueError):apply_override(self.track,self.original,self.export,'wrong','r1')
  self.d['rerun_idtracker']=True
  with self.assertRaises(ValueError):apply_override(self.track,self.original,self.export,'abc','r1')
if __name__=='__main__':unittest.main()
