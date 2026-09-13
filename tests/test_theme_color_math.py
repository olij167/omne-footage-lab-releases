import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app_source'))

from theme_color_math import contrast_ratio, normalize_hex, best_text_color  # noqa: E402


class ThemeColorMathTests(unittest.TestCase):
    def test_black_white_contrast_is_21(self):
        self.assertAlmostEqual(contrast_ratio('#000000', '#FFFFFF'), 21.0, places=6)

    def test_normalize_hex_is_canonical_uppercase(self):
        self.assertEqual(normalize_hex('#d7b04c'), '#D7B04C')
        self.assertEqual(normalize_hex('d7b04c'), '#D7B04C')
        with self.assertRaises(ValueError):
            normalize_hex('#abc')

    def test_best_text_color_chooses_measured_contrast(self):
        self.assertEqual(best_text_color('#FFFFFF', '#000000', '#FFFFFF'), '#000000')
        self.assertEqual(best_text_color('#000000', '#000000', '#FFFFFF'), '#FFFFFF')

    def test_approved_palette_gated_pairs_meet_reported_contrast(self):
        report_path = ROOT / 'tests' / 'fixtures' / 'contrast_report.json'
        report = json.loads(report_path.read_text(encoding='utf-8'))
        for theme_name, theme in report['themes'].items():
            for row in theme:
                if not row.get('release_gate', False):
                    continue
                pair_name = row['pair']
                actual = contrast_ratio(row['foreground'], row['background'])
                self.assertAlmostEqual(actual, float(row['ratio']), delta=0.02,
                                       msg=f'{theme_name}/{pair_name}')
                self.assertGreaterEqual(actual, 4.5, msg=f'{theme_name}/{pair_name}')

    def test_selection_foreground_is_valid_against_selection_and_tab_backgrounds(self):
        palette_path = ROOT / 'tests' / 'fixtures' / 'palette_seeds.json'
        data = json.loads(palette_path.read_text(encoding='utf-8'))
        for name, entry in data['themes'].items():
            chrome = entry['chrome']
            for bg_role in ('selection_bg', 'tab_selected_bg'):
                self.assertGreaterEqual(
                    contrast_ratio(chrome['selection_fg'], chrome[bg_role]),
                    4.5,
                    msg=f'{name}: selection_fg on {bg_role}',
                )


if __name__ == '__main__':
    unittest.main()
