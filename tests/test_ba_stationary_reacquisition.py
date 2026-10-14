import unittest
import numpy as np
from ba_stationary_reacquisition import propose
class StationaryTests(unittest.TestCase):
 def setup_case(self):
  im=np.zeros((200,250),np.uint8);im[65:96,85:116]=np.random.default_rng(7).integers(0,255,(31,31),dtype=np.uint8)
  xy=np.tile([100.,80.],(30,1));return xy,[im.copy()for _ in xy]
 def test_initial_wrong_reference_recovered(self):
  xy,ims=self.setup_case();xy[:3]=[210,140];p,a=propose(xy,ims,[0,0]);self.assertTrue(np.max(np.linalg.norm(p[:3]-[100,80],axis=1))<2)
 def test_clean_stationary_stays_exact(self):
  xy,ims=self.setup_case();p,a=propose(xy,ims,[0,0]);np.testing.assert_equal(p,xy)
 def test_short_occlusion_stays_unknown(self):
  xy,ims=self.setup_case();xy[3]=[210,140];xy[14:16]=[180,140];ims[14][:]=0;ims[15][:]=0;p,a=propose(xy,ims,[0,0]);self.assertTrue(np.isnan(p[14:16]).all());self.assertEqual(a['proposed_missing_indices'],[14,15])
 def test_protected_and_missing_not_overwritten(self):
  xy,ims=self.setup_case();xy[3]=[210,140];xy[10]=np.nan;protect=np.zeros(30,bool);protect[3]=True;p,a=propose(xy,ims,[0,0],protect);np.testing.assert_equal(p,xy)
 def test_moving_reference_abstains(self):
  xy,ims=self.setup_case();xy[:,0]=np.arange(30)*10;p,a=propose(xy,ims,[0,0]);np.testing.assert_equal(p,xy)
if __name__=='__main__':unittest.main()
