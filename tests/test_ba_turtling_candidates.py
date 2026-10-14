import unittest
import numpy as np
from ba_turtling_candidates import candidate_episodes

class ContinuityTests(unittest.TestCase):
 def test_onset_backtracks_to_transition_without_changing_baseline(self):
  a=np.zeros((240,2));a[:40,0]=-30
  base=np.zeros(240,bool);base[79:]=True
  r=candidate_episodes(a,base,1000,30)
  self.assertEqual(r['bouts'][0]['start_global_frame'],1040)
  self.assertEqual(r['baseline']['candidate_frames'],161)
  self.assertEqual(r['added_candidate_frames'],39)
  self.assertFalse(base[40]);self.assertIsNone(r['confirmed_overturned_seconds'])
 def test_stationarity_alone_does_not_create_an_episode(self):
  r=candidate_episodes(np.zeros((240,2)),[False]*240,0,30)
  self.assertEqual(r['candidate_frames'],0)
 def test_quiet_gap_bounded_by_anchors_is_provisional(self):
  base=np.ones(300,bool);base[140:150]=False
  r=candidate_episodes(np.zeros((300,2)),base,0,30)
  self.assertEqual(r['candidate_frames'],300)
  self.assertEqual(r['evidence'][140],'quiet_pause_hypothesis')
 def test_missing_jump_long_gap_and_trailing_pause_not_joined(self):
  for mode in ['missing','jump','long','trailing']:
   a=np.zeros((300,2));base=np.ones(300,bool);base[140:150]=False
   if mode=='missing':a[145]=np.nan
   if mode=='jump':a[145,0]=100
   if mode=='long':base[140:171]=False
   if mode=='trailing':base[140:]=False
   r=candidate_episodes(a,base,0,30)
   self.assertEqual(r['episode_mask'],base.tolist(),mode)
 def test_onset_does_not_cross_missing_or_extreme_jump(self):
  for mode in ['missing','large','drift']:
   a=np.zeros((240,2));a[:40,0]=-30;base=np.zeros(240,bool);base[79:]=True
   if mode=='missing':a[60]=np.nan
   if mode=='large':a[:40,0]=-300
   if mode=='drift':a[40:79,0]=np.linspace(-30,0,39)
   r=candidate_episodes(a,base,0,30)
   self.assertEqual(r['episode_mask'],base.tolist(),mode)
 def test_invalid_rules_and_baseline_missing_rejected(self):
  with self.assertRaises(ValueError):candidate_episodes([[float('nan'),0]],[True],0,30)
  with self.assertRaises(ValueError):candidate_episodes([[0,0]],[False],0,0)
if __name__=='__main__':unittest.main()
