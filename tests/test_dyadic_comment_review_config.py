"""No private inputs or media processing needed."""
import os
import unittest
from unittest.mock import patch
from pathlib import Path
import build_dyadic_comment_review as review

class ReviewConfigTests(unittest.TestCase):
    def test_unset_link_is_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(review.source_link(), '')

    def test_local_link_is_used(self):
        with patch.dict(os.environ, {'DYADIC_REVIEW_SOURCE_URL': ' https://example.invalid/source '}):
            self.assertEqual(review.source_link(), 'https://example.invalid/source')

    def test_source_has_no_embedded_access_key(self):
        self.assertNotIn('rlkey=', Path(review.__file__).read_text())

    def test_frame_inputs(self):
        self.assertEqual(review.parse_frames(''), [(None, None)])
        self.assertEqual(review.parse_frames('0'), [(0, 0)])
        self.assertEqual(review.parse_frames('115-120;125'), [(115, 120), (125, 125)])
        for invalid in ['120-115', 'not a frame']:
            with self.assertRaises(ValueError):
                review.parse_frames(invalid)

if __name__ == '__main__':
    unittest.main()
