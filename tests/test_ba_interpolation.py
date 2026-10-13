import unittest
import numpy as np
from ba_interpolation import frozen_interpolate,VERSION
class InterpolationTests(unittest.TestCase):
 def setUp(self):
  self.x=np.column_stack([np.arange(100.)*3+30,np.full(100,80.)]);self.p=np.zeros(100,bool);self.cfg={'roi':[[0,0],[500,0],[500,500],[0,500]]}
 def call(self,x=None,**kw):return frozen_interpolate(self.x if x is None else x,100,self.p,self.cfg,**dict(collection='BA',number_of_animals=1,**kw))
 def test_speed_not_total_distance(self):
  x=self.x.copy();x[20:50]=np.nan;y,m,e,a=self.call(x);np.testing.assert_allclose(y,self.x);self.assertGreater(e[0]['endpoint_distance_px'],60)
 def test_long_gap_missing(self):
  x=self.x.copy();x[20:51]=np.nan;y,*_=self.call(x);self.assertTrue(np.isnan(y[20:51]).all())
 def test_scope_guard(self):
  for c,n in [('BA',2),('BA',6),('BA',None),('BA',True),('dyadic',1),(None,1)]:
   with self.assertRaises(ValueError):frozen_interpolate(self.x,100,self.p,self.cfg,collection=c,number_of_animals=n)
 def test_preserve_existing_and_protected(self):
  x=self.x.copy();x[20:25]=np.nan;self.p[22]=True;y,*_=self.call(x);np.testing.assert_array_equal(y,x)
 def test_speed_reject(self):
  x=self.x.copy();x[20:22]=np.nan;x[22:]+=np.array([150,0]);y,*_=self.call(x);self.assertTrue(np.isnan(y[20:22]).all())
 def test_empty_control(self):
  y,m,e,a=self.call();np.testing.assert_array_equal(y,self.x);self.assertEqual(e,[])
 def test_partial_nan_retained(self):
  x=self.x.copy();x[20,0]=np.nan;y,m,e,a=self.call(x);np.testing.assert_array_equal(y[np.isfinite(x).all(1)],x[np.isfinite(x).all(1)])
if __name__=='__main__':unittest.main()
