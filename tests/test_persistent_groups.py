"""Contract regressions for Hannah's review and the shared 1.6.0 rules.

The former one-blob/confirmation/backtrace expectations are superseded:
finite input IDs must never be suppressed, moved, or classified as inferred.
"""
import unittest
import numpy as np
from persistent_groups import persistent_groups


def blob(x, ids=()):
    return dict(centroid=[x, 0], identities=list(ids))


class PersistentTests(unittest.TestCase):
    def check_raw(self, raw, result):
        known = np.isfinite(raw).all(axis=2)
        np.testing.assert_array_equal(result['xy'][known], raw[known])
        self.assertTrue((result['source'][known] == 'ASSIGNED').all())
        self.assertFalse(result['inferred'][known].any())
        for (a, b), mask in result['masks'].items():
            self.assertFalse((mask & known[:, a] & known[:, b]).any())

    def test_available_ids_preserved_with_shared_absent_or_ambiguous_blobs(self):
        raw = np.array([[[0, 0], [10, 0]], [[2, 0], [8, 0]],
                        [[0, 0], [90, 0]], [[500, 0], [510, 0]]], float)
        for blobs in ({}, {str(t): [blob(float(row[:, 0].mean()))]
                          for t, row in enumerate(raw)},
                      {str(t): [blob(-1), blob(1)] for t in range(4)}):
            with self.subTest(blobs=blobs):
                g = persistent_groups(raw, blobs)
                self.check_raw(raw, g)
                self.assertFalse(g['masks'][0, 1].any())

    def test_new_contact_requires_social_radius_not_movement_radius(self):
        for separation, expected in [(60, True), (60.01, False), (90, False)]:
            with self.subTest(separation=separation):
                r = np.array([[[0, 0], [separation, 0]],
                              [[np.nan, np.nan], [separation, 0]],
                              [[np.nan, np.nan], [separation, 0]]])
                b = {'0': [blob(0, (1,)), blob(separation, (2,))],
                     '1': [blob(separation, (2,))], '2': [blob(separation, (2,))]}
                g = persistent_groups(r, b)
                self.check_raw(r, g)
                self.assertEqual(bool(g['masks'][0, 1][1]), expected)
                if not expected:
                    self.assertTrue(np.isnan(g['xy'][1:, 0]).all())

    def test_stale_proximity_does_not_establish_new_contact(self):
        r = np.array([[[0, 0], [50, 0]], [[np.nan, np.nan], [np.nan, np.nan]],
                      [[np.nan, np.nan], [50, 0]]])
        g = persistent_groups(r, {'0': [blob(0), blob(50)], '2': [blob(50)]})
        self.check_raw(r, g)
        self.assertFalse(g['masks'][0, 1][2])
        self.assertTrue(np.isnan(g['xy'][2, 0]).all())

    def test_six_beetles_have_missing_only_psc_and_immediate_departure(self):
        r = np.array([[[0, 0], [30, 0], [500, 0], [520, 0], [900, 0], [1300, 0]]]*4, float)
        r[1:3, 0] = np.nan
        r[3, 0] = [700, 0]  # return far from inferred pile, no delay
        b = {str(t): [blob(30), blob(510), blob(900), blob(1300)] for t in range(4)}
        g = persistent_groups(r, b)
        self.check_raw(r, g)
        self.assertTrue(g['masks'][0, 1][1:3].all())
        self.assertFalse(g['masks'][0, 1][3])
        self.assertFalse(g['masks'][2, 3].any())
        self.assertEqual(g['source'][1, 0], 'PSCP_BLOB')
        self.assertEqual(g['source'][1, 1], 'ASSIGNED')

    def test_established_missing_group_survives_detection_gap_without_filling_it(self):
        r = np.full((6, 2, 2), np.nan)
        r[0] = [[0, 0], [10, 0]]
        b = {'0': [blob(5)], '1': [blob(7)], '2': [blob(9)],
             '3': [], '4': [blob(80)], '5': [blob(82)]}
        g = persistent_groups(r, b)
        self.check_raw(r, g)
        self.assertFalse(g['masks'][0, 1][0])
        self.assertTrue(g['masks'][0, 1][[1, 2, 4, 5]].all())
        self.assertTrue(np.isnan(g['xy'][3]).all())
        self.assertTrue(g['unresolved_masks'][0, 1][3])
        strict = persistent_groups(r, b, gap_radius_cap=65.)
        self.assertTrue(np.isnan(strict['xy'][4]).all())

    def test_raw_return_after_gap_works_even_without_detections(self):
        r = np.full((40, 2, 2), np.nan)
        r[0] = [[0, 0], [10, 0]]
        r[39] = [[1000, 0], [1500, 0]]
        g = persistent_groups(r, {'1': [blob(5)]})
        self.check_raw(r, g)
        self.assertFalse(g['masks'][0, 1][39])
        self.assertEqual(len([e for e in g['events'] if e['kind'] == 'RAW_ID_RETURNED']), 2)

    def test_single_frame_raw_return_is_not_overwritten_by_old_pile(self):
        r = np.full((5, 2, 2), np.nan)
        r[0] = [[0, 0], [2, 0]]
        r[2, 0] = [220, 0]
        b = {'0': [blob(1)], '1': [blob(3)], '2': [blob(5), blob(220)],
             '3': [blob(7)], '4': [blob(9)]}
        g = persistent_groups(r, b)
        self.check_raw(r, g)
        self.assertTrue(np.isnan(g['xy'][3:, 0]).all())
        self.assertFalse(g['masks'][0, 1][2:].any())

    def test_raw_swaps_and_shared_labels_are_retained_not_silently_corrected(self):
        r = np.array([[[0, 0], [2, 0], [800, 0]],
                      [[801, 0], [1, 0], [801, 0]]], float)
        g = persistent_groups(r, {'0': [blob(1), blob(800)],
                                   '1': [blob(1), blob(801)]})
        self.check_raw(r, g)
        self.assertFalse(g['inferred'].any())

    def test_missing_singleton_continuity_is_not_psc(self):
        r = np.array([[[0, 0], [500, 0]], [[np.nan, np.nan], [500, 0]]])
        g = persistent_groups(r, {'0': [blob(0), blob(500)],
                                   '1': [blob(10), blob(500)]})
        self.check_raw(r, g)
        self.assertEqual(g['source'][1, 0], 'BLOB_CONTINUITY')
        self.assertFalse(g['masks'][0, 1][1])

    def test_competing_candidates_leave_missing_id_unresolved(self):
        r = np.array([[[0, 0], [500, 0]], [[np.nan, np.nan], [500, 0]]])
        g = persistent_groups(r, {'1': [blob(-10), blob(10), blob(500)]})
        self.check_raw(r, g)
        self.assertTrue(np.isnan(g['xy'][1, 0]).all())
        self.assertTrue(g['ambiguous'][1, 0])

    def test_uninitialized_identity_is_not_invented(self):
        r = np.full((4, 2, 2), np.nan)
        r[:, 1] = [0, 0]
        g = persistent_groups(r, {str(t): [blob(0)] for t in range(4)})
        self.check_raw(r, g)
        self.assertTrue(np.isnan(g['xy'][:, 0]).all())
        self.assertFalse(g['masks'][0, 1].any())

    def test_long_gap_does_not_reacquire_missing_group(self):
        r = np.full((35, 2, 2), np.nan)
        r[0] = [[0, 0], [10, 0]]
        g = persistent_groups(r, {'1': [blob(5)], '34': [blob(6)]})
        self.assertTrue(np.isnan(g['xy'][34]).all())

    def test_never_mutates_input_or_detections(self):
        import copy
        r = np.array([[[0, 0], [10, 0]], [[np.nan, np.nan], [10, 0]]])
        b = {'0': [blob(5)], '1': [blob(10)]}
        before, blobs_before = r.copy(), copy.deepcopy(b)
        persistent_groups(r, b)
        np.testing.assert_array_equal(r, before)
        self.assertEqual(b, blobs_before)

    def test_all_missing_input_stays_missing(self):
        r = np.full((4, 6, 2), np.nan)
        g = persistent_groups(r, {str(t): [blob(0)] for t in range(4)})
        self.assertTrue(np.isnan(g['xy']).all())
        self.assertFalse(g['inferred'].any())


if __name__ == '__main__':
    unittest.main()
