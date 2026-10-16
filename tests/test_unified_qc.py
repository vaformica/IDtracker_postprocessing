import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import unified_qc as qc

class SharedQC(unittest.TestCase):
    def test_two_frame_flash_and_return(self):
        rng=np.random.default_rng(4);base=rng.integers(20,180,(90,160),dtype=np.uint8)
        self.assertFalse(qc.image_pair(base,base)['lighting_candidate'])
        self.assertTrue(qc.image_pair(base,base+30)['lighting_candidate'])
        self.assertTrue(qc.image_pair(base+30,base)['lighting_candidate'])
        self.assertFalse(qc.image_pair(base,base+30)['camera_motion_candidate'])
    def test_translation_is_separate(self):
        base=np.random.default_rng(2).integers(20,180,(90,160),dtype=np.uint8)
        r=qc.image_pair(base,np.roll(base,4,axis=1))
        self.assertTrue(r['camera_motion_candidate']);self.assertEqual(r['shift_x'],4)
        self.assertFalse(r['lighting_candidate'])
    def test_local_change_does_not_become_global_lighting(self):
        a=np.zeros((90,160));b=a.copy();b[:30,:40]=100
        self.assertFalse(qc.image_pair(a,b)['lighting_candidate'])
    def test_all_group_sizes_and_input_immutable(self):
        for n in [1,2,6]:
            a=np.zeros((10,n,2));a[4,:,0]=201;a[6,0]=np.nan;before=a.copy()
            r=qc.summarize(a,100,30)
            json.dumps(r,allow_nan=False)
            self.assertEqual(len(r['per_animal']),n);self.assertEqual(r['per_animal'][0]['missing_percent'],10)
            self.assertEqual(r['per_animal'][0]['raw_jump_steps'],2)
            self.assertEqual(any(e['kind']=='SYNCHRONOUS_RAW_JUMPS' for e in r['events']),n>1)
            np.testing.assert_equal(a,before)
    def test_gap_is_not_jump_and_exclusion_changes_denominator(self):
        a=np.zeros((5,1,2));a[1]=np.nan;a[2:]=500
        r=qc.summarize(a,10,30,excluded=[[11,11]])
        self.assertEqual(r['per_animal'][0]['raw_jump_steps'],0)
        self.assertEqual(r['per_animal'][0]['eligible_frames'],4)
        self.assertEqual(r['per_animal'][0]['missing_percent'],0)
        self.assertEqual(r['intentionally_excluded_frames'],1)
    def test_all_excluded_is_unknown(self):
        r=qc.summarize(np.zeros((2,1,2)),10,30,excluded=[[10,11]])
        self.assertIsNone(r['per_animal'][0]['missing_percent'])
    def test_invalid_ranges_and_shape(self):
        for ranges in [[[1,2]],[[10,12]],[[True,11]],[[11,10]]]:
            with self.assertRaises(ValueError):qc.summarize(np.zeros((2,1,2)),10,30,excluded=ranges)
        with self.assertRaises(ValueError):qc.summarize(np.zeros((2,2)),0,30)
    def test_video_events_scope_and_original_frames(self):
        m=dict(frame=101,previous_frame=100,**qc.image_pair(np.zeros((90,160)),np.ones((90,160))*50))
        r=qc.summarize(np.zeros((4,2,2)),100,30,video_scan=dict(status='ASSESSED',decoded_frames=104,metrics=[m]))
        e=next(e for e in r['events'] if e['kind']=='LIGHTING_CHANGE')
        self.assertEqual((e['first_global_frame'],e['last_global_frame_inclusive'],e['scope']),(100,101,'recording'))
        with self.assertRaises(ValueError):qc.summarize(np.zeros((4,1,2)),100,30,video_scan=dict(status='ASSESSED',decoded_frames=103,metrics=[]))
    def test_failure_never_looks_clean(self):
        r=qc.summarize(np.zeros((3,1,2)),0,30,video_scan=dict(status='FAILED',reason='decode'))
        self.assertFalse(r['assessment_complete']);self.assertEqual(r['recording_scan']['status'],'FAILED')
    def test_report_escaping_and_no_overwrite(self):
        a=np.zeros((3,1,2));r=qc.summarize(a,0,30);r['source']=dict(video='<script>bad</script>')
        with tempfile.TemporaryDirectory() as tmp:
            qc.write_report(tmp,r,a)
            s=(Path(tmp)/'unified_qc.html').read_text();self.assertNotIn('<script>bad',s);self.assertIn('NOT_ASSESSED',s)
            with self.assertRaises(FileExistsError):qc.write_report(tmp,r,a)
    def test_run_qc_records_failed_scan_without_clean_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);src=r/'trajectories.npy';np.save(src,{'trajectories':np.zeros((10,2,2))})
            with patch.object(qc,'scan_video',side_effect=RuntimeError('decode failure')):
                receipt=qc.run_qc(r/'output',src,r/'video.mp4',0,9,30)
            self.assertEqual(receipt['recording_status'],'FAILED')
            self.assertFalse(receipt['assessment_complete'])
            self.assertTrue((r/'output'/'unified_qc.html').is_file())
            self.assertEqual(receipt['dyadic_turtling_candidates']['candidate_bouts'],0)
            self.assertTrue((r/'output'/'dyadic_turtling_qc.json').is_file())
    def test_posture_sidecar_dyadic_only(self):
        for count in [1,6]:
            with tempfile.TemporaryDirectory() as tmp:
                r=Path(tmp);src=r/'trajectories.npy'
                np.save(src,{'trajectories':np.zeros((10,count,2))})
                receipt=qc.run_qc(r/'out',src,'unused.mp4',0,9,30,skip_video=True)
                self.assertIsNone(receipt['dyadic_turtling_candidates'])
                self.assertFalse((r/'out'/'dyadic_turtling_qc.json').exists())

if __name__=='__main__':unittest.main()
