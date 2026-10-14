import unittest
import numpy as np
from ba_turtling_continuity_experiment import refine, motion_signature, Rules

class ContinuityTests(unittest.TestCase):
    def fixture(self):
        # Frequent reversals provide a supported synthetic anchor followed by quiet.
        xy=np.zeros((500,2));xy[:180,0]=np.where(np.arange(180)%2,10.,-10.)
        base=np.zeros(500,bool);base[:180]=True
        return xy,base,np.ones(500,bool)
    def test_quiet_tail_persists(self):
        a,b,e=self.fixture();r=refine(a,b,e)
        self.assertTrue(all(r['candidate_mask']))
        self.assertEqual(r['evidence'][300],'localized_continuation_hypothesis')
    def test_smooth_circle_is_ambiguous_not_upright(self):
        t=np.linspace(0,8*np.pi,180);a=np.c_[25*np.cos(t),25*np.sin(t)]
        r=refine(a,np.ones(180,bool),np.ones(180,bool))
        self.assertFalse(any(r['candidate_mask']))
        self.assertTrue(all(r['ambiguous_loop_mask']))
        self.assertIsNone(r['confirmed_overturned_seconds'])
    def test_stationary_alone_cannot_start(self):
        a,b,e=self.fixture();b[:]=False
        self.assertFalse(any(refine(a,b,e)['candidate_mask']))
    def test_missing_breaks_continuation_no_interpolation(self):
        a,b,e=self.fixture();a[220]=np.nan
        r=refine(a,b,e)
        self.assertTrue(r['candidate_mask'][219]);self.assertFalse(any(r['candidate_mask'][220:]))
        self.assertEqual(r['evidence'][220],'tracking_unknown')
    def test_spatial_departure_ends_continuation(self):
        a,b,e=self.fixture();a[200:,0]=np.arange(300)
        r=refine(a,b,e)
        self.assertTrue(r['candidate_mask'][235]);self.assertFalse(any(r['candidate_mask'][236:]))
    def test_jump_ends_continuation(self):
        a,b,e=self.fixture();a[200,0]=25
        self.assertFalse(any(refine(a,b,e)['candidate_mask'][200:]))
    def test_no_chain_by_recent_inferred_positions(self):
        a,b,e=self.fixture();a[180:,0]=np.linspace(0,100,320)
        r=refine(a,b,e)
        self.assertLess(sum(r['candidate_mask']),400)
    def test_recovery_eligibility_enforced(self):
        a,b,e=self.fixture();e[200:]=False
        self.assertFalse(any(refine(a,b,e)['candidate_mask'][200:]))
        e[0]=False
        with self.assertRaises(ValueError):refine(a,b,e)
    def test_original_arrays_unchanged(self):
        a,b,e=self.fixture();aa=a.copy();bb=b.copy();ee=e.copy();refine(a,b,e)
        np.testing.assert_array_equal(a,aa);np.testing.assert_array_equal(b,bb);np.testing.assert_array_equal(e,ee)
    def test_short_fragment_requires_review(self):
        a,b,e=self.fixture();b[30:]=False
        r=refine(a,b,e)
        self.assertFalse(any(r['candidate_mask']));self.assertTrue(all(r['ambiguous_loop_mask'][:30]))
    def test_invalid_settings(self):
        a,b,e=self.fixture()
        for rules in [Rules(smooth_frames=10),Rules(continuation_radius_px=float('nan')),Rules(minimum_reversal_fraction=2)]:
            with self.assertRaises(ValueError):refine(a,b,e,rules=rules)
    def test_global_audit_inclusive_boundaries(self):
        a,b,e=self.fixture();r=refine(a,b,e,start=900)
        self.assertEqual(r['anchor_audit'][0]['first_global_frame'],900)
        self.assertEqual(r['anchor_audit'][0]['last_global_frame'],1079)

if __name__=='__main__':unittest.main()
