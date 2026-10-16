import unittest
import numpy as np
import dyadic_turtling_long_bouts as qc


class LongBoutScreen(unittest.TestCase):
    def looping(self, n=1000):
        t = np.arange(n) * .2
        return np.column_stack([10 * np.cos(t), 10 * np.sin(t)])

    def test_minimum_is_inclusive_and_gaps_split(self):
        m = np.r_[np.ones(299, bool), False, np.ones(300, bool)]
        self.assertEqual(qc.runs(qc.sustain(m)), [(300, 600)])

    def test_first100_and_absolute_frame_numbering(self):
        xy = self.looping()
        r = qc.summarize(np.stack([xy, xy], axis=1), np.zeros((1000, 2)), 55, 30)
        self.assertEqual(r['events'][0]['first_global_frame'], 155)
        self.assertEqual(r['events'][0]['last_global_frame_inclusive'], 1054)
        self.assertEqual(r['events'][0]['candidate_frames'], 900)

    def test_fungus_and_missing_never_flagged_or_bridged(self):
        xy = self.looping(1600)
        xy[700] = np.nan
        fungus = np.zeros(1600)
        fungus[1100:1110] = 1
        fungus[500] = np.nan
        mask, _, _, _ = qc.candidate_mask(xy, fungus)
        self.assertFalse(mask[700])
        self.assertFalse(mask[500])
        self.assertFalse(mask[1100:1110].any())
        self.assertTrue(all(b-a >= 300 for a, b in qc.runs(mask)))

    def test_quiet_alone_and_short_window_not_events(self):
        for n in [0, 100, 1000]:
            r = qc.summarize(np.zeros((n, 2, 2)), np.zeros((n, 2)), 0, 30)
            self.assertEqual(r['events'], [])

    def test_unsupported_fps_is_not_assessed(self):
        r = qc.summarize(np.zeros((500, 2, 2)), np.zeros((500, 2)), 0, 60)
        self.assertEqual(r['status'], 'NOT_ASSESSED')

    def test_does_not_mutate_inputs(self):
        xy = self.looping()
        raw = np.stack([xy, xy], axis=1)
        before = raw.copy()
        fungus = np.zeros((len(xy), 2))
        qc.summarize(raw, fungus, 0, 30)
        np.testing.assert_equal(raw, before)
        self.assertFalse(fungus.any())


if __name__ == '__main__':
    unittest.main()
