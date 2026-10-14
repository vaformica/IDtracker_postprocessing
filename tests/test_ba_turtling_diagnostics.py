import unittest
import numpy as np
from ba_turtling_diagnostics import window_features, gate_passes, mask_from_windows, confusion


class GateAuditTests(unittest.TestCase):
    def test_circle_is_candidate(self):
        angle = np.linspace(0, 8*np.pi, 120)
        xy = 10*np.column_stack((np.cos(angle), np.sin(angle)))
        features = window_features(xy)
        self.assertTrue(gate_passes(features).all())
        self.assertEqual(mask_from_windows(xy, [True]).sum(), 120)

    def test_stationary_and_straight_walk_rejected(self):
        for xy in [np.zeros((120, 2)), np.column_stack((np.arange(120)*2, np.zeros(120)))]:
            self.assertFalse(gate_passes(window_features(xy)).all())

    def test_missing_frames_never_filled(self):
        xy = np.zeros((121, 2)); xy[60] = np.nan
        mask = mask_from_windows(xy, [True, True])
        self.assertEqual(int(mask.sum()), 120)
        self.assertFalse(mask[60])
        self.assertTrue(mask[-1])

    def test_threshold_equality(self):
        self.assertTrue(gate_passes(np.array([[.95,20,120,5,3,.25]])).all())
        for i, value in enumerate([.949,20.01,119.9,4.99,2.99,.251]):
            row = np.array([[.95,20,120,5,3,.25]])
            row[0,i] = value
            self.assertFalse(gate_passes(row)[0,i])
        self.assertFalse(gate_passes(np.array([[1,0,120,35.01,3,.25]]))[0,3])

    def test_short_and_all_missing_inputs(self):
        self.assertEqual(window_features(np.zeros((119,2))).shape, (0,6))
        xy=np.full((120,2),np.nan)
        self.assertFalse(gate_passes(window_features(xy)).all())
        self.assertFalse(mask_from_windows(xy,[True]).any())

    def test_confusion(self):
        self.assertEqual(confusion(np.array([1,1,0,0],bool),np.array([1,0,1,0],bool)),
                         dict(tp=1,fp=1,tn=1,fn=1))


if __name__ == '__main__':
    unittest.main()
