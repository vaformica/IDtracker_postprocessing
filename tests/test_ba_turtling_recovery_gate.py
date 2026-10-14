import unittest
import numpy as np
from ba_turtling_recovery_gate import recovery_gate, gate_candidates


class RecoveryGateTests(unittest.TestCase):
    def test_exact_threshold_opens_on_confirmation_frame_not_first_departure(self):
        xy=np.vstack(([0,0],np.tile([30.,0],(30,1))))
        r=recovery_gate(xy,100)
        self.assertEqual(r['sustained_departure_start_global_frame'],101)
        self.assertEqual(r['confirmation_global_frame'],130)
        self.assertEqual(sum(r['eligible_mask']),1)

    def test_brief_displacement_does_not_open_gate(self):
        xy=np.zeros((100,2));xy[5]=[100,0]
        self.assertIsNone(recovery_gate(xy,100)['confirmation_global_frame'])

    def test_large_jumps_are_flagged_and_later_recovery_can_be_confirmed(self):
        xy=np.zeros((100,2));xy[2]=[500,0];xy[20:]=[40,0]
        r=recovery_gate(xy,100)
        self.assertEqual(r['excessive_step_landing_frames'],[102,103])
        self.assertEqual(r['confirmation_global_frame'],149)

    def test_missing_position_interrupts_confirmation(self):
        xy=np.vstack(([0,0],np.tile([40.,0],(70,1))));xy[15]=np.nan
        r=recovery_gate(xy,100)
        self.assertEqual(r['confirmation_global_frame'],146)
        self.assertEqual(r['state'][15],'tracking_uncertain')

    def test_missing_start_is_unknown(self):
        xy=np.ones((100,2))*40;xy[0]=np.nan
        r=gate_candidates(np.ones(100,bool),xy,100)
        self.assertEqual(r['status'],'UNKNOWN_MISSING_START_POSITION')
        self.assertFalse(any(r['candidate_mask']))
        self.assertTrue(all(s=='tracking_uncertain' for s in r['state']))

    def test_return_to_origin_does_not_close_gate_or_invent_candidates(self):
        xy=np.zeros((80,2));xy[1:40]=[40,0];before=xy.copy()
        mask=np.zeros(80,bool);mask[[5,70]]=True
        r=gate_candidates(mask,xy,100)
        self.assertEqual(np.flatnonzero(r['candidate_mask']).tolist(),[70])
        self.assertTrue(r['eligible_mask'][-1])
        self.assertTrue(np.array_equal(xy,before))
        self.assertIsNone(r['confirmed_overturned_seconds'])

    def test_invalid_parameters_rejected(self):
        for kw in [{'distance_px':0},{'fps':float('nan')},{'hold_seconds':-1}]:
            with self.assertRaises(ValueError):recovery_gate(np.zeros((40,2)),100,**kw)

    def test_known_camera_offset_cannot_establish_recovery(self):
        xy=np.zeros((100,2));xy[2:]=[100,0]
        r=recovery_gate(xy,100,initial_camera_artifact_frames=[102])
        self.assertEqual(r['status'],'UNKNOWN_CAMERA_REFERENCE_NOT_REACQUIRED')
        self.assertFalse(any(r['eligible_mask']))

    def test_json_null_coordinates_remain_missing(self):
        xy=[[None,None]]+[[0,0]]*40
        r=gate_candidates([True]*41,xy,100)
        self.assertEqual(r['status'],'UNKNOWN_MISSING_START_POSITION')
        self.assertFalse(any(r['candidate_mask']))

    def test_known_camera_bump_requires_reference_reacquisition(self):
        xy=np.zeros((110,2));xy[2]=[500,0];xy[60:]=[40,0]
        r=recovery_gate(xy,100,initial_camera_artifact_frames=[102,103])
        self.assertEqual(r['reference_reacquired_global_frame'],133)
        self.assertEqual(r['confirmation_global_frame'],189)


if __name__=='__main__':unittest.main()
