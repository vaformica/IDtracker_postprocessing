import unittest
import numpy as np
from ba_review_priority import assess, Rules

class ReviewTests(unittest.TestCase):
    def fixture(self,n=2000):
        xy=np.column_stack([np.arange(n)*.2,np.zeros(n)]);m=[False]*n
        a=dict(version='0.3.0-development',candidate_mask=m.copy(),ambiguous_loop_mask=m.copy(),evidence=['none']*n)
        b=dict(version='0.4.0-development',candidate_mask=m.copy(),evidence=['unchanged_03']*n,adjustments=[],rules={'onset_lookback_frames':300})
        return xy,np.ones(n,bool),a,b
    def run_case(self,case):return assess(case[0],100,case[1],case[2],case[3])
    def codes(self,r):return {f['code'] for f in r['flags']}
    def test_gap_inclusive_and_high(self):
        c=self.fixture();c[0][10:130]=np.nan;r=self.run_case(c);self.assertEqual(r['missing_intervals'],[[110,229]]);self.assertEqual(r['priority'],'high')
    def test_jump_not_bridged_across_missing(self):
        c=self.fixture();c[0][50:60]=np.nan;c[0][60:]+=500;r=self.run_case(c);self.assertEqual(r['metrics']['jump_count'],0);self.assertEqual(len(r['gap_returns']),1)
    def test_exact_jump_threshold(self):
        c=self.fixture(3);c[0][:]=[[0,0],[100,0],[301,0]];r=self.run_case(c);self.assertEqual(r['metrics']['jump_count'],1);self.assertEqual(r['metrics']['severe_jump_count'],1)
    def test_jump_denominator_available_only(self):
        c=self.fixture(5);c[0][:]=[[0,0],[101,0],[np.nan,np.nan],[0,0],[1,0]];r=self.run_case(c);self.assertEqual(r['metrics']['jump_percent_of_available_steps'],50)
    def test_all_missing_unknown(self):
        c=self.fixture();c[0][:]=np.nan;c[1][:]=False;r=self.run_case(c);self.assertIsNone(r['metrics']['max_adjacent_step_px']);self.assertIsNone(r['metrics']['jump_percent_of_available_steps']);self.assertIn('RECOVERY_UNRESOLVED',self.codes(r))
    def test_search_limit_flag(self):
        c=self.fixture();c[3]['adjustments']=[dict(kind='onset_extension',first_global_frame=400,last_global_frame=699)];r=self.run_case(c);self.assertIn('ONSET_SEARCH_LIMIT',self.codes(r));self.assertEqual(r['onset_search_limits'][0]['review_earlier_than'],400)
    def test_short_extension_not_cap(self):
        c=self.fixture();c[3]['adjustments']=[dict(kind='onset_extension',first_global_frame=400,last_global_frame=698)];self.assertNotIn('ONSET_SEARCH_LIMIT',self.codes(self.run_case(c)))
    def test_long_candidate_not_confirmed(self):
        c=self.fixture();c[3]['candidate_mask'][:1800]=[True]*1800;r=self.run_case(c);self.assertIn('LONG_TURTLING_CANDIDATE',self.codes(r));self.assertIsNone(r['confirmed_turtling_seconds']);self.assertIsNone(r['automatic_confidence_probability'])
    def test_ambiguous_union_not_double_counted(self):
        c=self.fixture();c[2]['ambiguous_loop_mask'][100:200]=[True]*100;c[3]['candidate_mask'][100:200]=[True]*100;r=self.run_case(c);self.assertEqual(r['metrics']['behavior_review_proxy_frames'],100)
    def test_missing_edge_never_implies_righting(self):
        c=self.fixture();c[3]['candidate_mask'][10:50]=[True]*40;c[0][50]=np.nan;r=self.run_case(c);self.assertIn('missing_after_end',r['boundary_concerns'][0]['reasons'])
    def test_exact_stationary_counts_positions(self):
        c=self.fixture(600);c[0][:]=0;r=self.run_case(c);self.assertIn('EXACT_STATIONARITY',self.codes(r));self.assertEqual(next(f['intervals'] for f in r['flags'] if f['code']=='EXACT_STATIONARITY'),[[100,699]])
    def test_no_flags_not_approval_and_immutable(self):
        c=self.fixture();before=c[0].copy();r=self.run_case(c);self.assertEqual(r['priority'],'spot_check');self.assertEqual(r['status'],'UNREVIEWED_HEURISTIC_PRIORITIES');np.testing.assert_array_equal(c[0],before)
    def test_invalid_shapes_and_rules(self):
        c=list(self.fixture());c[1]=np.ones(4,bool)
        with self.assertRaises(ValueError):self.run_case(c)
        c=self.fixture()
        with self.assertRaises(ValueError):assess(c[0],100,c[1],c[2],c[3],rules=Rules(missing_fraction=1.2))
    def test_candidates_cannot_fill_missing(self):
        c=self.fixture();c[0][0]=np.nan;c[3]['candidate_mask'][0]=True
        with self.assertRaises(ValueError):self.run_case(c)
if __name__=='__main__':unittest.main()
