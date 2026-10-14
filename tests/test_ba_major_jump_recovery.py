import unittest
import numpy as np
from ba_major_jump_recovery import propose
class MajorJumpTests(unittest.TestCase):
    def run_case(self, raw, candidate, statuses=None):
        return propose(raw,candidate,statuses or ['proposed_blob']*len(raw))
    def test_supported_out_and_back_repaired(self):
        r=np.array([[0,0],[200,0],[2,0]],float)
        p,m,_=self.run_case(r,[[0,0],[1,0],[2,0]])
        self.assertEqual(m.tolist(),[False,True,False]);self.assertEqual(p[1,0],1)
        self.assertEqual(r[1,0],200)
    def test_failed_recovery_preserves_original(self):
        r=np.array([[0,0],[200,0],[2,0]],float)
        p,m,_=self.run_case(r,np.full((3,2),np.nan))
        np.testing.assert_equal(p,r);self.assertFalse(m.any())
    def test_missing_stays_missing(self):
        r=np.array([[0,0],[np.nan,np.nan],[2,0]])
        p,m,_=self.run_case(r,[[0,0],[1,0],[2,0]])
        np.testing.assert_equal(p,r)
    def test_small_centroid_offsets_unchanged(self):
        r=np.array([[0,0],[1,0],[2,0]],float)
        p,m,_=self.run_case(r,r+10)
        np.testing.assert_equal(p,r)
    def test_wrong_rejoin_rejects_entire_patch(self):
        r=np.array([[0,0],[200,0],[210,0],[2,0]],float)
        p,m,a=self.run_case(r,[[0,0],[1,0],[80,0],[2,0]])
        np.testing.assert_equal(p,r);self.assertFalse(m.any())
    def test_major_distance_without_jump_is_not_enough(self):
        r=np.array([[0,0],[80,0],[0,0]],float)
        p,m,_=self.run_case(r,[[0,0],[1,0],[0,0]])
        np.testing.assert_equal(p,r)
    def test_unobserved_flank_and_unsupported_candidate(self):
        r=np.array([[0,0],[200,0],[2,0]],float)
        p,m,_=self.run_case(r,[[0,0],[1,0],[2,0]],['unchanged','unknown','unchanged'])
        np.testing.assert_equal(p,r)
        p,m,_=self.run_case([[200,0],[1,0]],[[0,0],[1,0]])
        self.assertFalse(m.any())
if __name__=='__main__':unittest.main()
