import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np

from build_canonical_review import build
from run_six_beetle_pipeline import arena_crop, find_trajectory
from six_beetle_firebird_gui import (
    DEFAULT_SESSION_ROOTS,
    DEFAULT_SSH_HOST,
    connection_error,
    pipeline_command,
    validated_parameters,
)


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
            manifest = json.loads((output / "source_manifest.json").read_text())
            self.assertEqual(manifest["canonical_sha256"], digest)
            self.assertEqual(manifest["status"], "UNREVIEWED")
            dyad = root / "dyad_analysis"
            dyad.mkdir()
            dyad_state = dyad / "canonical_states.npz"
            np.savez_compressed(dyad_state, raw=raw[:,:2], xy=xy[:,:2],
                inferred=inferred[:,:2], group_ids=group_ids[:,:2],
                source=source[:,:2], ambiguous=np.zeros((frames,2),dtype=bool))
            (dyad / "manifest.json").write_text(json.dumps(dict(
                settings={"start":100,"social_distance_threshold_px":60}, rois=rois[:2],
                output_sha256={dyad_state.name:hashlib.sha256(dyad_state.read_bytes()).hexdigest()})))
            dyad_html = build(dyad, video, root/"dyad_review", (0,0,800,600), 30, label="Dyad")
            dyad_payload = json.loads(re.search(r"const D=(.*);\nconst v=",dyad_html.read_text()).group(1))
            self.assertEqual(dyad_payload['pairs'],[[0,1]])
            self.assertEqual(len(dyad_payload['fungus'][0]),2)


class PipelineHelpersTests(unittest.TestCase):
    def test_gui_uses_established_firebird_alias_and_explains_vpn_failure(self):
        self.assertEqual(DEFAULT_SSH_HOST, "firebird")
        self.assertIn("managed_idtracker_runs", DEFAULT_SESSION_ROOTS)
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
        )
        parameters = validated_parameters(values)
        command = pipeline_command("/code", "/run", "/post/python", "/id/python", "/ffmpeg", "/ffprobe", parameters)
        joined = " ".join(command)
        self.assertIn("--proximity-px 61.0", joined)
        self.assertIn("--jump-threshold-px 201.0", joined)
        self.assertIn("--reconstruction-speed-px 99.0", joined)
        self.assertIn("--trajectory /remote/session/trajectories/validated.npy", joined)
        self.assertIn("--analysis-output /run/analysis", joined)
        self.assertIn("--review-output /run/review", joined)


if __name__ == "__main__":
    unittest.main()
