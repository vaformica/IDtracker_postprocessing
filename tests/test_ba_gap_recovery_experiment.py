import unittest
import numpy as np
from ba_gap_recovery_experiment import propose
class GapRecoveryTests(unittest.TestCase):
 def setUp(self):
  self.xy=np.column_stack([np.arange(60.)+20,np.full(60,50.)]);self.roi=[[0,0],[200,0],[200,200],[0,200]]
 def test_short_known_linear_path(self):
  x=self.xy.copy();x[20:25]=np.nan;y,m,a=propose(x,self.roi);np.testing.assert_allclose(y,self.xy);self.assertTrue((m[20:25]=='interpolated').all())
 def test_protected_gap_and_nearby_flank(self):
  x=self.xy.copy();x[20:25]=np.nan;p=np.zeros(60,bool);p[21]=True;y,m,a=propose(x,self.roi,protected=p);np.testing.assert_array_equal(y,x)
  p[:]=False;p[18]=True;y,m,a=propose(x,self.roi,protected=p);np.testing.assert_array_equal(y,x)
 def test_long_and_unbounded_stay_missing(self):
  x=self.xy.copy();x[10:35]=np.nan;x[50:]=np.nan;y,m,a=propose(x,self.roi);np.testing.assert_array_equal(y,x)
 def test_existing_coordinates_unchanged(self):
  y,m,a=propose(self.xy,self.roi);np.testing.assert_array_equal(y,self.xy)
 def test_large_jump_not_bridged(self):
  x=self.xy.copy();x[20:25]=np.nan;x[25:,0]+=60;y,m,a=propose(x,self.roi);np.testing.assert_array_equal(y,x)
 def test_outside_roi_not_filled(self):
  x=self.xy.copy();x[20:25]=np.nan;y,m,a=propose(x,[[0,0],[200,0],[200,40],[0,40]]);np.testing.assert_array_equal(y,x)
if __name__=='__main__':unittest.main()

class ImageBridgeTests(unittest.TestCase):
 def test_stationary_two_flank_image_recovery(self):
  rng=np.random.default_rng(45);im=np.full((120,120),180,np.uint8);im[45:76,45:76]=rng.integers(20,150,(31,31),dtype=np.uint8)
  xy=np.full((80,2),60.);xy[20:50]=np.nan
  y,m,a=propose(xy,[[0,0],[119,0],[119,119],[0,119]],{i:im for i in range(80)})
  self.assertTrue((m[20:50]=='image_candidate').all());np.testing.assert_allclose(y[20:50],60)
 def test_uniform_image_remains_missing(self):
  xy=np.full((80,2),60.);xy[20:50]=np.nan;im=np.full((120,120),180,np.uint8)
  y,m,a=propose(xy,[[0,0],[119,0],[119,119],[0,119]],{i:im for i in range(80)})
  self.assertTrue(np.isnan(y[20:50]).all())
