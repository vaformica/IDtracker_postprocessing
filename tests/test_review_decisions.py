import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from apply_review_decisions import replay
from build_canonical_review import build


class ReviewDecisionTests(unittest.TestCase):
    def test_review_replays_without_touching_raw_and_builds_portable_viewer(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);bundle=root/'analysis';bundle.mkdir()
            raw=np.array([[[5.,5.],[50.,5.]],[[15.,5.],[70.,5.]],[[25.,5.],[80.,5.]]])
            ids=np.tile(np.array([0,1]),(3,1))
            state=bundle/'canonical_states.npz'
            np.savez_compressed(state,raw=raw,xy=raw,inferred=np.zeros((3,2),bool),
                group_ids=ids,source=np.full((3,2),'ASSIGNED'),ambiguous=np.zeros((3,2),bool))
            sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            manifest=dict(settings=dict(start=10,social_distance_threshold_px=20),
                rois=[[[0,0],[100,0],[100,100],[0,100]],[[10,0],[30,0],[30,10],[10,10]]],
                output_sha256={'canonical_states.npz':sha(state)},
                reconstruction=dict(max_speed_px_per_frame=100))
            (bundle/'manifest.json').write_text(json.dumps(manifest))
            video=root/'clip.mp4';video.write_bytes(b'fake-video-for-portable-review-test')
            source_review=root/'review';build(bundle,video,source_review,(0,0,100,100),30,
                                             source_toml='/inputs/Camera_test_B2.toml')
            def decision(kind,value,a,b,frame):
                return dict(created_utc='2026-09-23T00:00:00Z',reviewer='Tester',reason='Visible in source clip',
                    kind=kind,value=value,animal_id=a,partner_id=b,start_frame=frame,end_frame_inclusive=frame)
            review=dict(schema='beetle-review-v1',analysis_manifest_sha256=sha(bundle/'manifest.json'),
                canonical_sha256=sha(state),frame_start=10,frame_end_inclusive=12,
                decisions=[decision('pscp','yes',1,0,11),decision('fungus','1',1,None,11),
                           decision('fungus','1',0,None,10),
                           decision('proximity','yes',0,1,12)])
            output=root/'reviewed';replay(bundle,review,output,source_review)
            with (output/'reviewed_frame_data.csv').open(newline='') as stream:
                rows=list(csv.DictReader(stream))
            at11=next(r for r in rows if r['global_frame']=='11' and r['animal_id']=='1')
            self.assertEqual((at11['raw_x'],at11['x'],at11['location_source']),('70.0','15.0','HUMAN_PSCP'))
            self.assertEqual((at11['fungus_1'],at11['human_intervention'],at11['pscp_partners']),('1','1','0'))
            step11=next(r for r in rows if r['global_frame']=='11' and r['animal_id']=='0')
            self.assertEqual(step11['step_midpoint_fungus_1'],'1')
            with (output/'reviewed_pair_summary.csv').open(newline='') as stream:
                pairs=list(csv.DictReader(stream))
            self.assertEqual((pairs[0]['pscp_frames'],pairs[0]['observed_proximity_frames']),('1','1'))
            self.assertEqual(sha(state),manifest['output_sha256']['canonical_states.npz'])
            review_files=json.loads((output/'review'/'source_manifest.json').read_text())
            self.assertEqual(review_files['cell_id'],'B2')
            self.assertEqual(review_files['html'],'Camera_test_B2__interaction_review.html')
            html=(output/'review'/review_files['html']).read_text()
            self.assertIn('Review and correct frames',html)
            self.assertIn('Visible in source clip',html)
            self.assertTrue((output/'review'/review_files['video']).is_file())
            with self.assertRaises(FileExistsError):replay(bundle,review,output)
            invalid=dict(review,decisions=[decision('fungus','1',1,None,11),
                                           decision('location','missing',1,0,11)])
            failed=root/'invalid_review'
            with self.assertRaisesRegex(ValueError,'Fungus correction needs a known coordinate'):
                replay(bundle,invalid,failed)
            self.assertFalse(failed.exists())
            self.assertFalse(list(root.glob('.beetle-review-*')))
