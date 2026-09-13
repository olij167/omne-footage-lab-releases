import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app_source'))
APP = ROOT / 'app_source' / 'omne_footage_lab.py'
spec = importlib.util.spec_from_file_location('retrospector_app_for_tests', APP)
app = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = app
spec.loader.exec_module(app)


class BuiltinThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seeds = json.loads((ROOT / 'tests' / 'fixtures' / 'palette_seeds.json').read_text(encoding='utf-8'))

    def test_builtin_order_and_default_match_approved_library(self):
        self.assertEqual(list(app.BUILTIN_THEMES), self.seeds['published_order'])
        defaults = app.profile_defaults()
        self.assertEqual(defaults['published_themes'], self.seeds['published_order'])
        self.assertEqual(defaults['default_theme'], 'Pungent Funk')

    def test_builtin_chrome_matches_seed_values_exactly(self):
        for name in self.seeds['published_order']:
            expected = self.seeds['themes'][name]['chrome']
            self.assertEqual(app.BUILTIN_THEMES[name], expected)

    def test_retired_preference_migrates_when_no_local_collision(self):
        aliases = self.seeds['aliases']
        for retired, current in aliases.items():
            self.assertEqual(app.resolve_theme_preference(retired, {}, list(app.BUILTIN_THEMES)), current)

    def test_local_retired_name_collision_wins(self):
        local = {'Pungent Purple': dict(app.DEFAULT_CHROME)}
        self.assertEqual(
            app.resolve_theme_preference('Pungent Purple', local, list(app.BUILTIN_THEMES)),
            'Pungent Purple',
        )

    def test_unrelated_local_theme_is_preserved(self):
        local = {'My Theme': dict(app.DEFAULT_CHROME)}
        self.assertEqual(app.resolve_theme_preference('My Theme', local, list(app.BUILTIN_THEMES)), 'My Theme')

    def test_unknown_preference_falls_back_to_default(self):
        self.assertEqual(app.resolve_theme_preference('No Such Theme', {}, list(app.BUILTIN_THEMES)), 'Pungent Funk')


if __name__ == '__main__':
    unittest.main()

class PreferenceMigrationIntegrationTests(unittest.TestCase):
    def test_loaded_preferences_migrate_retired_theme_before_binding_tk_variable(self):
        from omne_footage_lab import normalize_loaded_preferences
        values = normalize_loaded_preferences({'theme_name': 'Pungent Purple'}, {}, list(app.PUBLISHED_THEME_ORDER))
        self.assertEqual(values['theme_name'], 'Pungent Funk')
