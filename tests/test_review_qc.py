import unittest
import numpy as np
from build_review_qc_packages import calculate,bouts
class ReviewQC(unittest.TestCase):
 def test_thresholds_and_gap_categories(self):
  raw=np.array([[[0.,0]],[[100.,0]],[[200.001,0]],[[np.nan,np.nan]],[[500.,0]],[[700.0001,0]]])
  n=dict(raw=raw,xy=raw,inferred=np.zeros((6,1),bool),ambiguous=np.zeros((6,1),bool),identity_conflict=np.zeros((6,1),bool))
  s,e=calculate(n,175,30)
  self.assertEqual(s['raw_jumps_over_100'],2);self.assertEqual(s['raw_jumps_over_200'],1);self.assertEqual(s['distant_returns_over_100'],1)
  self.assertEqual([r['first_global_frame'] for r in e],[177,179,180]);self.assertEqual(e[1]['previous_global_frame'],177)
 def test_bouts_and_percentages(self):
  raw=np.full((60,2,2),np.nan);raw[:,0]=[1,2];xy=raw.copy();xy[:30,1]=[1,2]
  inferred=np.zeros((60,2),bool);inferred[:30,1]=True
  n=dict(raw=raw,xy=xy,inferred=inferred,ambiguous=np.zeros((60,2),bool),identity_conflict=np.zeros((60,2),bool))
  s,e=calculate(n,10,30)
  self.assertEqual(s['raw_missing_percent'],50);self.assertEqual(s['inferred_percent'],25);self.assertEqual(s['unresolved_percent'],25)
  self.assertEqual(s['long_missing_bouts'],1);self.assertEqual(s['long_psc_bouts'],1)
  self.assertEqual(bouts([True,True,False,True]),[(0,1),(3,3)])
if __name__=='__main__':unittest.main()
