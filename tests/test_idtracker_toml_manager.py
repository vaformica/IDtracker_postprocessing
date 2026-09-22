import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from firebird_idtracker_runner import verified_sessions

from idtracker_toml_manager import (
    common_fields,
    safe_label,
    submission_command,
    update_common_fields,
    validate_six_beetle_toml,
)


SAMPLE = '''name = "trial"
video_paths = [
  "/remote/video.mp4",
]
intensity_ths = [51, 255]
area_ths = [562.0, inf]
tracking_intervals = [[250, 16998]]
number_of_animals = 6
use_bkg = true
roi_list = ["arena [[0,0],[1,1]]", "f1", "f2", "f3"]
background_subtraction_stat = "median"
'''


class TomlManagerTests(unittest.TestCase):
    def test_verified_sessions_requires_complete_position_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            session = output / "session"
            trajectory_dir = session / "trajectories"
            trajectory_dir.mkdir(parents=True)
            (session / "session.json").write_text("{}")
            self.assertEqual(verified_sessions(output), [])
            points = np.full((2, 6, 2), np.nan)
            points[0, 0, 0] = 1.0
            np.save(trajectory_dir / "trajectories.npy", points)
            self.assertEqual(verified_sessions(output), [])
            points[0, 0, 1] = 2.0
            np.save(trajectory_dir / "trajectories.npy", points)
            self.assertEqual(verified_sessions(output), [str(session)])

    def test_validates_six_animals_and_four_rois(self):
        parsed = validate_six_beetle_toml(SAMPLE)
        self.assertEqual(parsed["number_of_animals"], 6)
        self.assertEqual(len(parsed["roi_list"]), 4)
        with self.assertRaisesRegex(ValueError, "must be 6"):
            validate_six_beetle_toml(SAMPLE.replace("number_of_animals = 6", "number_of_animals = 2"))
        with self.assertRaisesRegex(ValueError, "three fungus"):
            validate_six_beetle_toml(SAMPLE.replace(', "f3"', ""))

    def test_common_editor_preserves_rois_and_unknown_fields(self):
        original_rois = validate_six_beetle_toml(SAMPLE)["roi_list"]
        changed = update_common_fields(SAMPLE, {
            "name": "edited", "video_paths": ["/remote/new.mp4"],
            "intensity_min": "50", "intensity_max": "255",
            "area_min": "250", "area_max": "inf", "start": "422", "end": "7622",
            "animals": "6", "use_bkg": False,
        })
        parsed = validate_six_beetle_toml(changed)
        self.assertEqual(parsed["roi_list"], original_rois)
        self.assertEqual(parsed["background_subtraction_stat"], "median")
        self.assertEqual(parsed["tracking_intervals"], [[422, 7622]])
        self.assertFalse(parsed["use_bkg"])
        self.assertTrue(math.isinf(parsed["area_ths"][1]))
        self.assertIn("area_ths = [250.0, inf]", changed)
        self.assertEqual(common_fields(changed)["name"], "edited")

    def test_rejects_mixed_integer_and_float_area_array(self):
        with self.assertRaisesRegex(ValueError, "two float values"):
            validate_six_beetle_toml(SAMPLE.replace("[562.0, inf]", "[562, inf]"))

    def test_submission_command_and_safe_label(self):
        command = submission_command("/env", "/run/runner.py", "/run/input.toml", "/run/output")
        self.assertEqual(command[0], "/env/bin/python")
        self.assertIn("--track", "idtrackerai --track")
        self.assertEqual(safe_label("Box 1 / OLD"), "Box_1_OLD")


if __name__ == "__main__":
    unittest.main()
