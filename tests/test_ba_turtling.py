import unittest
from ba_turtling import summarize, summarize_review, apply_posture_review
class BoutTests(unittest.TestCase):
 def test_missing_splits_and_denominator(self):
  r=summarize([1,1,0,1],[1,1,0,1],100,2)
  self.assertEqual(r['candidate_seconds'],1.5)
  self.assertEqual(r['candidate_fraction_detected'],1)
  self.assertEqual(r['unknown_seconds'],.5)
  self.assertEqual([(b['start_global_frame'],b['end_global_frame_inclusive']) for b in r['bouts']],[(100,101),(103,103)])
  self.assertTrue(all(b['left_censored'] and b['right_censored'] for b in r['bouts']))
 def test_zero_detection_is_unknown_not_zero_posture(self):
  r=summarize([0,0],[0,0],12,30)
  self.assertIsNone(r['candidate_fraction_detected']);self.assertIsNone(r['confirmed_overturned_seconds'])
 def test_reject_missing_candidate(self):
  with self.assertRaises(ValueError):summarize([1],[0],1,30)
 def test_bout_boundaries_and_no_smoothing(self):
  r=summarize([0,1,0,1,1,0],[1]*6,7,10)
  self.assertEqual(r['bout_count'],2);self.assertEqual(r['longest_bout_seconds'],.2)
  self.assertFalse(any(b['left_censored'] or b['right_censored'] for b in r['bouts']))
class ReviewTests(unittest.TestCase):
 def test_overlaps_count_once_and_unknown_remains(self):
  n=dict(decision='confirmed_overturned',reviewer='V',reason='visible posture',first_global_frame=10,last_global_frame=14)
  r=summarize_review([n,n],10,19,10)
  self.assertEqual(r['confirmed_overturned_seconds'],.5)
  self.assertEqual(r['posture_unresolved_seconds'],.5)
 def test_conflicts_not_silently_overwritten(self):
  n=dict(decision='confirmed_overturned',reviewer='V',reason='posture',first_global_frame=10,last_global_frame=14)
  with self.assertRaises(ValueError):summarize_review([n,dict(n,decision='rejected_overturned')],10,19,10)
class PostureCorrectionTests(unittest.TestCase):
 def test_full_clip_overturned_includes_quiet_start_and_end(self):
  m=[0,0,1,0,1,0]
  n=dict(decision='confirmed_overturned',reviewer='Vince',reason='always on back',first_global_frame=100,last_global_frame=105)
  r=apply_posture_review(m,[1]*6,100,2,[n])
  self.assertEqual(r['status'],'FULL_WINDOW_POSTURE_REVIEW')
  self.assertEqual(r['episode_seconds'],3)
  self.assertEqual(r['baseline']['candidate_seconds'],1)
  self.assertEqual(r['episode_mask'],[True]*6)
  self.assertEqual(r['review']['posture_unresolved_seconds'],0)
  self.assertTrue(r['bouts'][0]['left_censored'])
  self.assertTrue(r['bouts'][0]['right_censored'])
  self.assertEqual(m,[0,0,1,0,1,0])
 def test_only_reviewed_pause_is_joined(self):
  m=[1,1,0,0,1,1,0,1]
  n=dict(decision='confirmed_overturned',reviewer='Vince',reason='still on back',first_global_frame=12,last_global_frame=13)
  r=apply_posture_review(m,[1]*8,10,30,[n,dict(n,decision='inactive_flailing')])
  self.assertEqual(m,[1,1,0,0,1,1,0,1])
  self.assertEqual(r['episode_mask'],[True]*6+[False,True])
  self.assertEqual(len(r['bouts']),2)
  self.assertEqual(r['baseline']['candidate_frames'],5)
  self.assertAlmostEqual(r['review']['observed_inactive_flailing_seconds'],2/30)
 def test_human_rejection_overrides_candidate(self):
  n=dict(decision='rejected_overturned',reviewer='V',reason='upright',first_global_frame=10,last_global_frame=10)
  r=apply_posture_review([1,1],[1,1],10,30,[n])
  self.assertEqual(r['episode_mask'],[False,True])
 def test_human_posture_without_tracking_is_explicit(self):
  n=dict(decision='confirmed_overturned',reviewer='V',reason='visible',first_global_frame=10,last_global_frame=10)
  r=apply_posture_review([0],[0],10,30,[n])
  self.assertEqual(r['evidence'],['human_confirmed_overturned'])
  self.assertAlmostEqual(r['baseline']['unknown_seconds'],1/30)
if __name__=='__main__':unittest.main()
