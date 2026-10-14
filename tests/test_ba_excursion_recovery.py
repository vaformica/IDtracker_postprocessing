import unittest
import numpy as np
from ba_excursion_recovery import propose
class ExcursionTests(unittest.TestCase):
 def run_case(self,raw,agreed,fw=None,bw=None,images=None):
  n=len(raw);blank=np.full((n,2),np.nan)
  return propose(np.array(raw,float),np.array(agreed,float),blank if fw is None else np.array(fw,float),blank if bw is None else np.array(bw,float),['proposed_blob']*n,images or [np.zeros((300,300),np.uint8)]*n,[0,0])
 def test_includes_short_leadin_only_with_major_excursion(self):
  raw=[[50,50],[80,50],[200,50],[50,50]];c=[[50,50]]*4
  p,m,a=self.run_case(raw,c);np.testing.assert_equal(p,c)
 def test_no_major_jump_no_change(self):
  raw=[[50,50],[80,50],[100,50],[50,50]]
  p,m,a=self.run_case(raw,[[50,50]]*4);np.testing.assert_equal(p,raw)
 def test_directional_candidate_needs_appearance(self):
  raw=[[50,50],[200,50],[50,50]]
  p,m,a=self.run_case(raw,[[np.nan,np.nan]]*3,bw=[[50,50]]*3);np.testing.assert_equal(p,raw)
 def test_directional_image_supported_patch(self):
  raw=[[50,50],[200,50],[50,50]]
  rng=np.random.default_rng(7);im=np.zeros((300,300),np.uint8);im[35:66,35:66]=rng.integers(0,255,(31,31),dtype=np.uint8)
  p,m,a=self.run_case(raw,[[np.nan,np.nan]]*3,bw=[[50,50]]*3,images=[im]*3);np.testing.assert_equal(p,[[50,50]]*3)
 def test_missing_and_existing_repair_preserved(self):
  raw=[[50,50],[200,50],[50,50],[np.nan,np.nan]];c=[[50,50],[51,50],[50,50],[52,50]]
  p,m,a=self.run_case(raw,c);self.assertEqual(p[1,0],51);self.assertTrue(np.isnan(p[3]).all())
 def test_failed_return_keeps_original(self):
  raw=[[50,50],[200,50],[90,50]];c=[[50,50],[50,50],[90,50]]
  p,m,a=self.run_case(raw,c);np.testing.assert_equal(p,raw)
if __name__=='__main__':unittest.main()
