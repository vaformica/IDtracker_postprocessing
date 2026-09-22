import unittest
import numpy as np
from reviewed_contacts import follow_detected_pile

class PileTests(unittest.TestCase):
 def test_group_survives_identity_loss_and_true_detection_gap(self):
  x=np.full((6,6,2),np.nan)
  x[0,[4,5]]=[[10,0],[11,0]]
  x[4,4]=[14,0]
  blobs={'0':[dict(centroid=[10,0],identities=[5,6])],
         '1':[dict(centroid=[11,0],identities=[None])],
         '2':[dict(centroid=[12,0],identities=[None])],
         '4':[dict(centroid=[14,0],identities=[5])],
         '5':[dict(centroid=[15,0],identities=[5])]}
  p,s,e=follow_detected_pile(x,blobs,[4,5],0,5,[10,0])
  self.assertTrue(np.isnan(p[3]).all())
  for t in [0,1,2,4,5]:np.testing.assert_array_equal(p[t,0],p[t,1])
  self.assertEqual(s[4,1],'PSCP_DETECTED_BLOB')

 def test_ambiguous_detections_are_missing(self):
  x=np.full((1,6,2),np.nan)
  b={'0':[dict(centroid=[1,0],identities=[None]),dict(centroid=[2,0],identities=[None])]}
  p,_,_=follow_detected_pile(x,b,[4,5],0,0,[0,0])
  self.assertTrue(np.isnan(p).all())

if __name__=='__main__':unittest.main()
