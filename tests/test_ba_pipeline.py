import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from run_ba_pipeline import source_config, frame_rows
from review_geometry import plan_review_geometry
import ba_qc

class BATests(unittest.TestCase):
    def test_inclusive_window_and_source_roi(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config='number_of_animals=1\ntracking_intervals=[[100,8000]]\nvideo_paths=["/remote/ba.mp4"]\nroi_list=[[[0,0],[100,0],[100,100],[0,100]]]\n'
            (root/'ba.toml').write_text(config)
            session=dict(number_of_animals=1,tracking_intervals=[[100,8000]],video_paths=['/remote/ba.mp4'],roi_list=[[[0,0],[100,0],[100,100],[0,100]]])
            (root/'session.json').write_text(json.dumps(session))
            _,start,end,_=source_config(root/'ba.toml',root)
            self.assertEqual((start,end,end-start+1),(100,7299,7200))
            session['roi_list'][0][0]=[1,1]
            (root/'session.json').write_text(json.dumps(session))
            with self.assertRaisesRegex(ValueError,'arena do not match'):source_config(root/'ba.toml',root)

    def test_missing_and_jump_break_distance_but_keep_locations(self):
        xy=np.array([[10.,10.],[20,10],[np.nan,np.nan],[50,50],[500,500],[60,50]])
        arena=np.array([[0,0],[1000,0],[1000,1000],[0,1000]])
        rows=list(frame_rows(xy,arena,100))
        self.assertEqual(sum(r['step_distance_px'] for r in rows if r['step_distance_px']!=''),10)
        self.assertEqual(sum(r['rejected_jump_step'] for r in rows),2)
        self.assertEqual(rows[4]['location_known'],1)
        self.assertEqual(rows[4]['in_arena_interior'],1)
        self.assertEqual(rows[2]['location_known'],0)
        self.assertEqual(rows[3]['step_from_previous_accepted'],0)

    def test_ba_video_preserves_orientation_and_aspect(self):
        g=plan_review_geometry([np.array([[0,0],[300,0],[300,400]])],(0,0,300,400))
        self.assertEqual(g['rotation_cw'],0)
        self.assertTrue(g['aspect_preserved'])
        self.assertAlmostEqual(g['content_width']/g['content_height'],.75,delta=.003)

    def test_qc_flags_missing_baseline_and_reports_global_episode(self):
        xy=np.full((200,2),np.nan)
        arena=np.array([[0,0],[100,0],[100,100],[0,100]])
        qc=ba_qc.summarize(list(frame_rows(xy,arena,123)),{'threshold_crossing_global_frame':''})
        self.assertIn('BASELINE_MISSING',qc['flags'])
        self.assertIn('LONGEST_MISSING_FRAMES',qc['flags'])
        self.assertEqual(qc['metrics']['longest_missing_frames'],200)
        self.assertIsNone(qc['metrics']['rejected_jump_fraction'])
        self.assertEqual(qc['episodes'][0]['start_global_frame'],123)
        self.assertEqual(qc['episodes'][0]['end_global_frame_inclusive'],322)

if __name__=='__main__':unittest.main()
