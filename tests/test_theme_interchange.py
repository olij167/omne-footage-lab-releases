import json
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app_source'))

from builtin_themes import BUILTIN_THEMES  # noqa: E402
from theme_interchange import (  # noqa: E402
    MAX_THEME_BYTES,
    ThemeImportError,
    detect_theme_format,
    export_native_theme,
    import_theme_bytes,
)


class ThemeInterchangeTests(unittest.TestCase):
    def test_native_examples_round_trip_complete_chrome(self):
        for path in sorted((ROOT / 'tests/fixtures/themes').glob('*.omne-theme.json')):
            imported = import_theme_bytes(path.name, path.read_bytes())
            self.assertEqual(imported.chrome, BUILTIN_THEMES[imported.name])
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / 'roundtrip.omne-theme.json'
                export_native_theme(out, imported.name, imported.appearance, imported.chrome,
                                    extensions={'test': {'value': 1}}, overwrite=False)
                again = import_theme_bytes(out.name, out.read_bytes())
                self.assertEqual(again.chrome, imported.chrome)
                self.assertEqual(again.extensions['test']['value'], 1)

    def test_rejects_over_one_mebibyte_without_parsing(self):
        with self.assertRaises(ThemeImportError):
            import_theme_bytes('too-big.json', b' ' * (MAX_THEME_BYTES + 1))

    def test_bad_native_format_rejects(self):
        payload = json.dumps({'format': 'wrong', 'version': 1}).encode()
        with self.assertRaises(ThemeImportError):
            import_theme_bytes('bad.omne-theme.json', payload)

    def test_base16_fixture_maps_deterministically_and_preserves_light_aware_text(self):
        path = ROOT / 'tests/fixtures/space-funk-base16.yaml'
        imported = import_theme_bytes(path.name, path.read_bytes())
        self.assertEqual(imported.source_format, 'base16')
        self.assertEqual(imported.chrome['background'], '#11131B')
        self.assertEqual(imported.chrome['accent'], '#7AA2F7')
        self.assertGreaterEqual(imported.contrast['selection'], 4.5)

    def test_base16_rejects_yaml_anchors_tags_and_nesting(self):
        for raw in (b'base00: &bad "111111"\n', b'base00: !tag 111111\n', b'palette:\n  base00: 111111\n'):
            with self.assertRaises(ThemeImportError):
                import_theme_bytes('bad.yaml', raw)

    def test_vscode_jsonc_keeps_double_slash_inside_strings_and_trailing_commas(self):
        raw = br'''{
          // comment
          "name": "URL // preserved",
          "colors": {
            "editor.background": "#11131B",
            "editor.foreground": "#DCE1F2",
            "input.background": "#0D0F16",
            "button.background": "#252A3B",
            "button.foreground": "#DCE1F2",
            "list.activeSelectionBackground": "#465A8C",
            "list.activeSelectionForeground": "#FFFFFF",
            "focusBorder": "#7AA2F7",
          },
          "tokenColors": [{"settings":{"foreground":"#BB9AF7"}}],
          "homepage": "https://example.com/a//b",
        }'''
        imported = import_theme_bytes('theme.jsonc', raw)
        self.assertEqual(imported.source_format, 'vscode')
        self.assertEqual(imported.source_metadata['name'], 'URL // preserved')
        self.assertEqual(imported.chrome['background'], '#11131B')
        self.assertEqual(imported.chrome['accent'], '#7AA2F7')

    def test_textmate_uses_global_settings_before_scoped_syntax(self):
        data = {
            'name': 'TextMate Test',
            'settings': [
                {'settings': {'background': '#11131B', 'foreground': '#DCE1F2', 'selection': '#465A8C'}},
                {'scope': 'keyword', 'settings': {'foreground': '#BB9AF7'}},
            ],
        }
        raw = plistlib.dumps(data)
        imported = import_theme_bytes('sample.tmTheme', raw)
        self.assertEqual(imported.source_format, 'textmate')
        self.assertEqual(imported.chrome['background'], '#11131B')
        self.assertEqual(imported.chrome['foreground'], '#DCE1F2')
        self.assertEqual(imported.chrome['selection_bg'], '#465A8C')
        self.assertEqual(imported.chrome['secondary_accent'], '#BB9AF7')

    def test_gpl_fixture_is_labelled_as_derived(self):
        path = ROOT / 'tests/fixtures/space-funk.gpl'
        imported = import_theme_bytes(path.name, path.read_bytes())
        self.assertEqual(imported.source_format, 'gimp-gpl')
        self.assertTrue(any(d.code == 'palette-derived' for d in imported.diagnostics))
        self.assertGreaterEqual(imported.contrast['main'], 4.5)

    def test_detection_uses_content_and_extension_safely(self):
        self.assertEqual(detect_theme_format('x.omne-theme.json', b'{"format":"omne.footage-lab.theme","version":1}'), 'native')
        self.assertEqual(detect_theme_format('x.tmTheme', plistlib.dumps({'settings': []})), 'textmate')
        self.assertEqual(detect_theme_format('x.gpl', b'GIMP Palette\nName: x\n0 0 0 Black\n'), 'gimp-gpl')


if __name__ == '__main__':
    unittest.main()
