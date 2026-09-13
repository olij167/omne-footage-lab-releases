import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app_source'))

import omne_footage_lab as app  # noqa: E402
from builtin_themes import BUILTIN_THEMES, DEFAULT_THEME_NAME, PUBLISHED_THEME_ORDER  # noqa: E402


class UiProfileAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads((ROOT / 'app_source/ui_profile.json').read_text(encoding='utf-8'))

    def test_profile_preserves_latest_authored_surface_depth(self):
        self.assertGreaterEqual(len(self.profile.get('labels', {})), 160)
        self.assertGreaterEqual(len(self.profile.get('tooltips', {})), 97)
        self.assertGreaterEqual(len(self.profile.get('elements', {})), 115)
        self.assertGreaterEqual(len(self.profile.get('messages', {})), 90)

    def test_profile_uses_retrospector_identity_but_preserves_owner_support_link(self):
        self.assertEqual(self.profile['schema'], 3)
        self.assertEqual(self.profile['identity']['app_name'], 'OmN-e Retrospector')
        self.assertEqual(self.profile['identity']['support_url'], 'https://ko-fi.com/pungentfunk')

    def test_profile_has_exact_approved_theme_library_and_default(self):
        self.assertEqual(self.profile['published_themes'], list(PUBLISHED_THEME_ORDER))
        self.assertEqual(self.profile['default_theme'], DEFAULT_THEME_NAME)
        self.assertEqual(self.profile['themes'], BUILTIN_THEMES)
        self.assertEqual(self.profile['chrome'], BUILTIN_THEMES[DEFAULT_THEME_NAME])

    def test_profile_validates_and_user_copy_is_rebranded(self):
        validated = app.validate_ui_profile(self.profile)
        self.assertEqual(validated['identity']['app_name'], 'OmN-e Retrospector')
        user_copy = json.dumps({k: self.profile[k] for k in ('identity','labels','tooltips','messages')}, ensure_ascii=False)
        self.assertNotIn('Footage Lab', user_copy)


if __name__ == '__main__':
    unittest.main()
