import unittest
import numpy as np
from ba_turtling_episode_experiment import experiment
from ba_turtling_diagnostics import gate_passes, mask_from_windows


class EpisodeExperimentTests(unittest.TestCase):
    def test_weaker_motion_cannot_create_unanchored_event(self):
        xy=np.zeros((120,2))
        features=np.array([[1,2,80,10,4,.1]])
        result=experiment(xy,np.zeros(120,bool),100,features=features)
        self.assertFalse(any(result['episode_mask']))

    def terminal_fixture(self,missing=False):
        xy=np.zeros((150,2))
        if missing:xy[-1]=np.nan
        features=np.tile([1,0,0,0,0,1.],(31,1))
        features[0]=[1,2,130,10,4,.1]
        base=mask_from_windows(xy,gate_passes(features).all(1))
        return xy,base,features

    def test_bounded_terminal_continuation_is_explicit_hypothesis(self):
        xy,base,features=self.terminal_fixture()
        result=experiment(xy,base,100,features=features)
        self.assertEqual(result['candidate_frames'],150)
        self.assertEqual(result['evidence'][-1],'short_terminal_continuation_hypothesis')
        self.assertIsNone(result['confirmed_overturned_seconds'])
        self.assertTrue(result['bouts'][-1]['right_censored'])

    def test_missing_tail_blocks_continuation(self):
        xy,base,features=self.terminal_fixture(missing=True)
        result=experiment(xy,base,100,features=features)
        self.assertEqual(result['candidate_frames'],120)

    def test_incompatible_baseline_rejected(self):
        xy,base,features=self.terminal_fixture();base[0]=False
        with self.assertRaises(ValueError):experiment(xy,base,100,features=features)

    def test_wrong_frame_rate_rejected(self):
        with self.assertRaises(ValueError):experiment(np.zeros((120,2)),np.zeros(120,bool),100,fps=25)


if __name__=='__main__':unittest.main()
