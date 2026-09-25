import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from build_canonical_review import build
from rebuild_raw_psc_compare_reviews import analyzed_frame_bounds, rebuild_task
from review_geometry import (legacy_review_geometry, plan_review_geometry,
                             review_filter, transform_point)
from run_six_beetle_pipeline import arena_crop, find_trajectory
from six_beetle_firebird_gui import (
    DEPLOY_FILES,
    DEFAULT_SESSION_ROOTS,
    DEFAULT_SSH_HOST,
    REMOTE_DISCOVERY,
    connection_error,
    pipeline_command,
    validated_parameters,
)


class FrameBoundsTests(unittest.TestCase):
    def test_interval_window_includes_both_endpoint_frames(self):
        self.assertEqual(analyzed_frame_bounds({'start': 220, 'window': 16777}),
                         (220, 16997, 16778))

    def test_documented_no_blob_dyadic_task_has_no_viewer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task = root / 'tasks' / 'excluded-cell'
            task.mkdir(parents=True)
            (task / 'final_status.json').write_text(
                json.dumps({'stage': 'EXCLUDED_TRACKING_NO_BLOBS'}))
            self.assertEqual(
                rebuild_task(root, 'dyadic', {'id': 'excluded-cell'}, 'ffmpeg'),
                'EXCLUDED excluded-cell: EXCLUDED_TRACKING_NO_BLOBS')


class PortableReviewTests(unittest.TestCase):
    def test_review_uses_canonical_piles_and_copies_video(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bundle = root / "analysis"
            bundle.mkdir()
            frames = 4
            raw = np.zeros((frames, 6, 2), dtype=float)
            for animal in range(6):
                raw[:, animal] = [100 + animal * 100, 200]
            raw[1, 0] = [100, 400]
            xy = raw.copy()
            xy[2, 5] = xy[2, 4]
            source = np.full((frames, 6), "ASSIGNED", dtype="<U24")
            source[2, 5] = "PSCP_BLOB"
            inferred = source == "PSCP_BLOB"
            group_ids = np.tile(np.arange(6), (frames, 1))
            group_ids[2, 5] = group_ids[2, 4]
            state = bundle / "canonical_states.npz"
            np.savez_compressed(
                state,
                raw=raw,
                xy=xy,
                inferred=inferred,
                group_ids=group_ids,
                source=source,
                ambiguous=np.zeros((frames, 6), dtype=bool),
            )
            rois = [
                [[0, 0], [800, 0], [800, 600], [0, 600]],
                [[50, 350], [150, 350], [150, 450], [50, 450]],
                [[350, 350], [450, 350], [450, 450], [350, 450]],
                [[650, 350], [750, 350], [750, 450], [650, 450]],
            ]
            digest = hashlib.sha256(state.read_bytes()).hexdigest()
            (bundle / "manifest.json").write_text(
                json.dumps(
                    dict(
                        settings={"start": 100},
                        rois=rois,
                        cell_label="BoxA",
                        video="source.mp4",
                        script_version="0.8.1-group",
                        persistent_model_version="1.5.1",
                        output_sha256={state.name: digest},
                    )
                )
            )
            video = root / "clip.mp4"
            video.write_bytes(b"portable-video-test")
            output = root / "review"
            html = build(bundle, video, output, (0, 0, 800, 600), 30, label="Trial A")
            self.assertTrue(html.is_file())
            self.assertTrue((output / "review_video.mp4").is_file())
            self.assertFalse((output / "review_video.mp4").is_symlink())
            self.assertEqual((output / "review_video.mp4").read_bytes(), video.read_bytes())
            text = html.read_text()
            self.assertIn("Trial A", text)
            self.assertNotIn("OLD_source_crop.mp4", text)
            payload = json.loads(re.search(r"const D=(.*);\nconst v=", text).group(1))
            pair_index = payload["pairs"].index([4, 5])
            self.assertEqual(payload["pairStates"][pair_index][2], 2)
            self.assertEqual(payload["rawPairStates"][pair_index][2], 0)
            self.assertEqual(payload["rawFungus"][1][0], 1)
            self.assertIn('id="rawMode"', text)
            self.assertIn('D.raw[t][a]', text)
            self.assertEqual((payload["pscModelVersion"], payload["processorVersion"]),
                             ("1.5.1", "0.8.1-group"))
            manifest = json.loads((output / "source_manifest.json").read_text())
            self.assertEqual(manifest["canonical_sha256"], digest)
            self.assertEqual(manifest["status"], "UNREVIEWED")
            self.assertEqual(manifest["review_view_version"], "raw-psc-compare-v3")
            self.assertEqual(manifest["analysis_frame_count"], 4)
            self.assertFalse(manifest['video_geometry']['aspect_preserved'])
            oriented_geometry = plan_review_geometry(rois, (0, 0, 800, 600))
            oriented_html = build(bundle, video, root / 'review_oriented',
                                  (0, 0, 800, 600), 30,
                                  video_geometry=oriented_geometry)
            oriented_payload = json.loads(re.search(
                r"const D=(.*);\nconst v=", oriented_html.read_text()).group(1))
            self.assertEqual(oriented_payload['videoGeometry'], oriented_geometry)
            self.assertTrue(json.loads((root/'review_oriented/source_manifest.json').read_text())
                            ['video_geometry']['aspect_preserved'])
            dyad = root / "dyad_analysis"
            dyad.mkdir()
            dyad_state = dyad / "canonical_states.npz"
            dyad_raw=raw[:,:2].copy();dyad_xy=xy[:,:2].copy()
            dyad_source=source[:,:2].copy();dyad_ids=group_ids[:,:2].copy()
            dyad_raw[2,1]=np.nan;dyad_xy[2,1]=dyad_xy[2,0]
            dyad_source[2,1]='PSCP_BLOB';dyad_ids[2,1]=dyad_ids[2,0]
            np.savez_compressed(dyad_state, raw=dyad_raw, xy=dyad_xy,
                inferred=dyad_source=='PSCP_BLOB', group_ids=dyad_ids,
                source=dyad_source, ambiguous=np.zeros((frames,2),dtype=bool))
            (dyad / "manifest.json").write_text(json.dumps(dict(
                settings={"start":100,"social_distance_threshold_px":60}, rois=rois[:2],
                output_sha256={dyad_state.name:hashlib.sha256(dyad_state.read_bytes()).hexdigest()})))
            dyad_html = build(dyad, video, root/"dyad_review", (0,0,800,600), 30, label="Dyad")
            dyad_payload = json.loads(re.search(r"const D=(.*);\nconst v=",dyad_html.read_text()).group(1))
            self.assertEqual(dyad_payload['pairs'],[[0,1]])
            self.assertEqual(len(dyad_payload['fungus'][0]),2)
            self.assertEqual(dyad_payload['pairStates'][0][2],2)


class PipelineHelpersTests(unittest.TestCase):
    def test_firebird_deployment_includes_review_geometry(self):
        self.assertIn('review_geometry.py', DEPLOY_FILES)

    def test_vertical_fungus_rois_rotate_individually_without_stretch(self):
        crop = (2740, 546, 860, 1190)
        arena = [[2740, 546], [3600, 546], [3600, 1736], [2740, 1736]]
        def fungus(cy):
            return [[3100, cy-40], [3200, cy-40], [3200, cy+40], [3100, cy+40]]
        for centers, expected_rotation in (((1460, 1110, 790), 90),
                                           ((790, 1110, 1460), 270)):
            rois = [arena] + [fungus(cy) for cy in centers]
            geometry = plan_review_geometry(rois, crop)
            self.assertEqual(geometry['rotation_cw'], expected_rotation)
            points = [transform_point((3150, cy), geometry) for cy in centers]
            self.assertLess(points[0][0], points[1][0])
            self.assertLess(points[1][0], points[2][0])
            self.assertLess(abs(points[0][1]-points[2][1]), 2)
            self.assertTrue(geometry['aspect_preserved'])
            self.assertAlmostEqual(geometry['content_width']/crop[3],
                                   geometry['content_height']/crop[2], delta=0.003)
            self.assertIn('transpose=clock' if expected_rotation == 90
                          else 'transpose=cclock', review_filter(0, 9, geometry))
        self.assertFalse(legacy_review_geometry(crop)['aspect_preserved'])
        wide_crop = (0, 0, 1200, 800)
        wide_arena = [[0, 0], [1200, 0], [1200, 800], [0, 800]]
        def horizontal_fungus(cx):
            return [[cx-30, 350], [cx+30, 350], [cx+30, 450], [cx-30, 450]]
        self.assertEqual(plan_review_geometry(
            [wide_arena] + [horizontal_fungus(x) for x in (200, 600, 1000)],
            wide_crop)['rotation_cw'], 0)
        self.assertEqual(plan_review_geometry(
            [wide_arena] + [horizontal_fungus(x) for x in (1000, 600, 200)],
            wide_crop)['rotation_cw'], 180)

    def test_group_discovery_filters_dyadic_and_six_profiles(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for count, rois in ((2,2),(6,4)):
                session = root/str(count)
                session.mkdir()
                (session/'session.json').write_text(json.dumps(dict(number_of_animals=count,
                    roi_list=[[[0,0],[10,0],[10,10],[0,10]]]*rois,
                    tracking_intervals=[[100,200]], video_paths=['video.mp4'])))
                (session/'trajectories.npy').write_bytes(b'test')
            def discover(profile):
                proc = subprocess.run([sys.executable,'-c',REMOTE_DISCOVERY],
                    input=json.dumps(dict(roots=[str(root)],profile=profile)),
                    text=True,capture_output=True,check=True)
                return json.loads(proc.stdout)
            self.assertEqual([r['animal_count'] for r in discover('dyadic')],[2])
            self.assertEqual([r['animal_count'] for r in discover('six')],[6])
            self.assertEqual({r['animal_count'] for r in discover('all')},{2,6})

    def test_gui_uses_established_firebird_alias_and_explains_vpn_failure(self):
        self.assertEqual(DEFAULT_SSH_HOST, "firebird")
        self.assertIn("managed_idtracker_runs", DEFAULT_SESSION_ROOTS)
        self.assertIn("2026_Fights_Recorded", DEFAULT_SESSION_ROOTS)
        message = connection_error(
            "ssh: Could not resolve hostname firebird.swarthmore.edu", "firebird"
        )
        self.assertIn("~/.ssh/config", message)
        self.assertIn("Swarthmore VPN", message)

    def test_trajectory_preference_and_even_arena_crop(self):
        with tempfile.TemporaryDirectory() as folder:
            session = Path(folder)
            (session / "trajectories").mkdir()
            (session / "trajectories" / "trajectories.npy").write_bytes(b"raw")
            (session / "trajectories" / "validated.npy").write_bytes(b"validated")
            self.assertEqual(find_trajectory(session).name, "validated.npy")
        rois = [np.array([[1.2, 3.1], [98.2, 3.1], [98.2, 79.9], [1.2, 79.9]])]
        x, y, width, height = arena_crop(rois, 100, 80, padding=7)
        self.assertEqual((x % 2, y % 2, width % 2, height % 2), (0, 0, 0, 0))
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_gui_command_preserves_all_scientific_thresholds(self):
        values = dict(
            session="/remote/session",
            trajectory="/remote/session/trajectories/validated.npy",
            video="/remote/video.mp4",
            label="Box 01",
            start="422",
            end="7622",
            fps="30",
            movement="30",
            wall="30",
            fungus="30",
            proximity="61",
            jump="201",
            reconstruction="99",
            split_confirmation="2",
            gap_speed="25",
            gap_cap="280",
            gap_frames="20",
            distant_confirmation="12",
        )
        parameters = validated_parameters(values)
        command = pipeline_command("/code", "/run", "/post/python", "/id/python", "/ffmpeg", "/ffprobe", parameters)
        joined = " ".join(command)
        self.assertIn("--proximity-px 61.0", joined)
        self.assertIn("--jump-threshold-px 201.0", joined)
        self.assertIn("--reconstruction-speed-px 99.0", joined)
        self.assertIn("--split-confirmation-frames 2", joined)
        self.assertIn("--gap-speed-px 25.0", joined)
        self.assertIn("--gap-radius-cap-px 280.0", joined)
        self.assertIn("--max-reacquire-gap-frames 20", joined)
        self.assertIn("--distant-confirmation-frames 12", joined)
        self.assertIn("--trajectory /remote/session/trajectories/validated.npy", joined)
        self.assertIn("--analysis-output /run/analysis", joined)
        self.assertIn("--review-output /run/review", joined)


if __name__ == "__main__":
    unittest.main()
