import unittest
from ba_science_selection import eligibility, select_versions


class SelectionTests(unittest.TestCase):
    def test_replacement_never_duplicates_parent(self):
        runs = [dict(dataset='old', run_id='a'), dict(dataset='new', run_id='a')]
        edge = dict(parent_dataset='old', parent_run='a', child_dataset='new', child_run='a')
        self.assertEqual(select_versions(runs, [edge]), [('new', 'a')])
        self.assertEqual(eligibility(dict(status='recommend_exclusion'), 'NO_LARGE_JUMP_BLOCK'), (False, False))

    def test_forks_and_cycles_fail_closed(self):
        runs = [dict(dataset=x, run_id='a') for x in ['old', 'new', 'other']]
        edge = lambda a, b: dict(parent_dataset=a, parent_run='a', child_dataset=b, child_run='a')
        for edges in [[edge('old', 'new'), edge('old', 'other')], [edge('old', 'new'), edge('new', 'old')]]:
            with self.assertRaises(ValueError): select_versions(runs, edges)

    def test_approval_is_not_implicit_movement_override(self):
        d = dict(status='usable_skim', movement_override=False)
        self.assertEqual(eligibility(d, 'BLOCKED_UNRESOLVED_JUMPS'), (True, False))
        self.assertEqual(eligibility(d, 'NO_LARGE_JUMP_BLOCK'), (True, True))
        d.update(movement_override=True, effective_movement_status='HUMAN_OVERRIDE_USE_STRICT_TRACK', review_does_not_clear_analysis_hold=False)
        self.assertEqual(eligibility(d, 'BLOCKED_UNRESOLVED_JUMPS'), (True, True))
        d['rerun_idtracker'] = True
        self.assertEqual(eligibility(d, 'BLOCKED_UNRESOLVED_JUMPS'), (True, False))


if __name__ == '__main__': unittest.main()
