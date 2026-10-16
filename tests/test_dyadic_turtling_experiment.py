import unittest, math
from dyadic_turtling_experiment import screen
class ScreenTests(unittest.TestCase):
 def test_quiet_is_candidate_not_posture(self):
  r=screen([[[0,0],[100,0]]]*120,0)
  self.assertEqual(set(r['states']),{'QUIET_REVIEW_CANDIDATE'})
 def test_partner_missing_abstains(self):
  r=screen([[[0,0],[None,None]]]*120,0)
  self.assertEqual(set(r['states']),{'INTERACTION_AMBIGUOUS'})
 def test_near_boundary_inclusive(self):
  self.assertEqual(set(screen([[[0,0],[60,0]]]*120,0)['states']),{'INTERACTION_AMBIGUOUS'})
 def test_missing_not_quiet(self):
  raw=[[[0,0],[100,0]] for _ in range(120)];raw[60][0]=[None,None]
  r=screen(raw,0);self.assertFalse(any(r['quiet']));self.assertEqual(r['states'][60],'TRACKING_UNKNOWN')
 def test_jump_blocks_quiet(self):
  raw=[[[0,0],[100,0]] for _ in range(120)];raw[60][0]=[100,100]
  self.assertFalse(any(screen(raw,0)['quiet']))
 def test_motion_is_not_quiet(self):
  self.assertFalse(any(screen([[[i,0],[1000,0]] for i in range(120)],0)['quiet']))
 def test_loop_and_quiet_distinct(self):
  raw=[[[15*math.cos(i),15*math.sin(i)],[300,0]] for i in range(120)]
  r=screen(raw,0);self.assertTrue(all(r['loop']));self.assertFalse(any(r['quiet']))
 def test_shape_rejected(self):
  with self.assertRaises(ValueError):screen([[[0,0]]]*120,0)
if __name__=='__main__':unittest.main()
