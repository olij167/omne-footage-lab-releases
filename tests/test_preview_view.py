import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app_source'))

from preview_view import compute_preview_transform, clamp_zoom  # noqa: E402


class PreviewViewTests(unittest.TestCase):
    def test_fit_expands_small_proxy_to_fill_available_cell_without_cropping(self):
        t = compute_preview_transform((426, 240), (852, 600), mode='fit')
        self.assertAlmostEqual(t.scale, 2.0)
        self.assertEqual(t.display_size, (852, 480))
        self.assertEqual(t.offset, (0, 0))

    def test_fit_preserves_aspect_ratio_for_tall_cell(self):
        t = compute_preview_transform((1920, 1080), (600, 800), mode='fit')
        self.assertEqual(t.display_size, (600, 338))
        self.assertAlmostEqual(t.scale, 600 / 1920)

    def test_actual_size_is_exactly_one_source_pixel_per_display_pixel(self):
        t = compute_preview_transform((426, 240), (852, 600), mode='actual')
        self.assertEqual(t.scale, 1.0)
        self.assertEqual(t.display_size, (426, 240))
        self.assertEqual(t.offset, (0, 0))

    def test_zoom_is_relative_to_fit_and_pan_is_clamped_to_visible_bounds(self):
        t = compute_preview_transform((426, 240), (852, 600), mode='zoom', zoom=2.0, pan=(9999, -9999))
        self.assertEqual(t.display_size, (1704, 960))
        self.assertEqual(t.offset, (426, -180))

    def test_pan_is_zero_when_scaled_image_is_smaller_than_viewport(self):
        t = compute_preview_transform((426, 240), (852, 600), mode='actual', pan=(50, 50))
        self.assertEqual(t.offset, (0, 0))

    def test_zoom_range_is_bounded(self):
        self.assertEqual(clamp_zoom(0.01), 0.25)
        self.assertEqual(clamp_zoom(99), 8.0)
        self.assertEqual(clamp_zoom(1.25), 1.25)


if __name__ == '__main__':
    unittest.main()
