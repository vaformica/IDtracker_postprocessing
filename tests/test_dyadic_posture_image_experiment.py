import unittest
import numpy as np
from dyadic_posture_image_experiment import crop,center_in_review,features,fit,predict
class ImageTests(unittest.TestCase):
 def setUp(self):self.g=dict(crop=[0,0,200,200],rotation_cw=0,content_width=200,content_height=200,pad_x=0,pad_y=0)
 def test_missing_center_abstains(self):self.assertEqual(crop(np.zeros((200,200),dtype=np.uint8),[None,None],self.g)[1],'missing_raw_center')
 def test_edge_abstains(self):self.assertIsNone(crop(np.zeros((200,200),dtype=np.uint8),[10,10],self.g)[0])
 def test_native_center(self):self.assertEqual(center_in_review([100,80],self.g),(100,80))
 def test_rotation(self):
  self.g['rotation_cw']=90;self.assertEqual(center_in_review([100,80],self.g),(120,100))
 def test_image_features_finite(self):
  p=np.ones((48,48))*.7;p[15:30,20:28]=.1
  x=features([p,p,p]);self.assertEqual(len(x),76);self.assertTrue(np.isfinite(x).all())
 def test_temporal_features_change(self):
  p=np.ones((48,48))*.7;q=p.copy();q[15:30,20:28]=.1
  self.assertFalse(np.array_equal(features([p,p,p]),features([q,p,q])))
 def test_training_requires_two_classes(self):
  with self.assertRaises(ValueError):fit([[0],[1]],[1,1],['a','b'])
 def test_model_separates_synthetic_signal(self):
  m=fit([[-2],[-1],[1],[2]],[0,0,1,1],['a','b','a','b']);p=predict(m,[[-2],[2]]);self.assertLess(p[0],.5);self.assertGreater(p[1],.5)
if __name__=='__main__':unittest.main()
