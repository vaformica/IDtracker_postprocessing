import unittest
from unittest.mock import patch
import numpy as np
from ba_combined_recovery import recovery_policy,recover
class PolicyTests(unittest.TestCase):
 def test_split_protected_and_long_window(self):
  raw=np.zeros((400,2));raw[50:52]=200;protected=np.zeros(400,bool);protected[50]=True
  windows,skipped=recovery_policy(raw,1000,protected)
  self.assertFalse(skipped);self.assertTrue(windows)
  self.assertTrue(all(not protected[a:b].any() for a,b in windows))
  raw[::2]=200;windows,skipped=recovery_policy(raw,1000,protected)
  self.assertFalse(windows);self.assertEqual(skipped,[[1000,1399]])
 def test_clean_control_unchanged(self):
  raw=np.column_stack([np.arange(50)*.1+50,np.full(50,50.)]);images=[np.zeros((100,100),np.uint8) for _ in raw]
  out,audit=recover(raw,raw.copy(),raw.copy(),raw.copy(),['kept_original']*50,images,[0,0],0,np.zeros(50,bool))
  np.testing.assert_array_equal(raw,out)
 def test_stationary_unknown_allowed_without_filling_raw_gaps(self):
  raw=np.zeros((100,2));raw[50]=200;images=[np.zeros((100,100),np.uint8) for _ in raw]
  def mask(x,images,origin,protected):
   out=x.copy();out[10]=np.nan;return out,{}
  with patch('ba_combined_recovery.excursions',return_value=(raw.copy(),np.zeros(100,bool),{})),patch('ba_combined_recovery.stationary',side_effect=mask):
   out,_=recover(raw,raw,raw,raw,['unchanged']*100,images,[0,0],0,np.zeros(100,bool))
  self.assertLess(np.isfinite(out).all(1).sum(),len(raw))
if __name__=='__main__':unittest.main()
