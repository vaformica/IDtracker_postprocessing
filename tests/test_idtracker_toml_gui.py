import unittest

from idtracker_toml_gui import App


SAMPLE = '''name = "trial"
video_paths = ["/remote/video.mp4"]
intensity_ths = [51, 255]
area_ths = [562.0, inf]
tracking_intervals = [[250, 16998]]
number_of_animals = 6
use_bkg = true
roi_list = ["arena", "f1", "f2", "f3"]
'''


class Variable:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class Text:
    def __init__(self):
        self.value = ""

    def delete(self, *_args):
        self.value = ""

    def insert(self, *_args):
        self.value = _args[-1]

    def get(self, *_args):
        return self.value


class Editor:
    source_text = {}
    staged_text = {}
    draft_text = {}
    current_path = ""
    loading_editor = False

    def __init__(self):
        self.source_text = {}
        self.staged_text = {}
        self.draft_text = {}
        self.raw = Text()
        self.fields = {key: Variable() for key in (
            "path", "name", "videos", "intensity_min", "intensity_max", "area_min",
            "area_max", "start", "end", "animals", "roi_count", "sha256")}
        self.use_bkg = Variable()


class GUIStagingTests(unittest.TestCase):
    def test_loading_toml_updates_background_checkbox(self):
        editor = Editor()
        editor.use_bkg.set(True)
        App._show_toml(editor, "source.toml", SAMPLE.replace("use_bkg = true", "use_bkg = false"), {"sha256": "abc"})
        self.assertFalse(editor.use_bkg.value)
        self.assertEqual(editor.fields["start"].value, "250")

    def test_unvalidated_raw_edit_is_draft_not_submission(self):
        editor = Editor()
        App._show_toml(editor, "source.toml", SAMPLE, {"sha256": "abc"})
        editor.raw.value = SAMPLE.replace("use_bkg = true", "use_bkg = false")
        App._capture_current(editor)
        self.assertIn("source.toml", editor.draft_text)
        self.assertNotIn("source.toml", editor.staged_text)


if __name__ == "__main__":
    unittest.main()
