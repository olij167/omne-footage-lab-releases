import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app_source'))

import omne_footage_lab as app  # noqa: E402


class RetrospectorIdentityTests(unittest.TestCase):
    def test_user_facing_identity_is_retrospector_v040(self):
        self.assertEqual(app.APP, 'OmN-e Retrospector')
        self.assertEqual(app.VERSION, '0.4.0')
        self.assertEqual(app.DEFAULT_IDENTITY['app_name'], 'OmN-e Retrospector')

    def test_technical_update_and_storage_identity_remain_footage_lab_compatible(self):
        self.assertEqual(app.TECHNICAL_APP_ID, 'omne-footage-lab')
        self.assertEqual(app.LEGACY_DATA_NAME, 'OmN-e Footage Lab')
        self.assertEqual(app.UPDATE_MANIFEST_URL, 'https://omne.space/downloads/footage-lab/update.json')

    def test_default_user_facing_copy_no_longer_calls_product_footage_lab(self):
        values = [app.APP, app.DEFAULT_IDENTITY['app_name'], *app.DEFAULT_LABELS.values(), *app.DEFAULT_TOOLTIPS.values()]
        self.assertFalse(any('Footage Lab' in str(value) for value in values))

    def test_native_linux_update_platform_uses_deb_asset_without_breaking_source_updates(self):
        self.assertEqual(app.native_update_platform('Linux', 'x86_64', False), 'linux')
        self.assertEqual(app.native_update_platform('Linux', 'x86_64', True), 'linux-x64')
        self.assertEqual(app.native_update_platform('Linux', 'aarch64', True), 'linux-arm64')
        self.assertEqual(app.native_update_platform('Windows', 'AMD64', True), 'windows-x64')
        self.assertEqual(app.native_update_platform('Darwin', 'arm64', True), 'macos-arm64')

    def test_linux_deb_is_a_native_installer_kind_only_on_linux(self):
        self.assertTrue(app.native_installer_kind_supported('deb', 'Linux'))
        self.assertFalse(app.native_installer_kind_supported('deb', 'Windows'))
        self.assertTrue(app.native_installer_kind_supported('msi', 'Windows'))
        self.assertTrue(app.native_installer_kind_supported('pkg', 'Darwin'))


if __name__ == '__main__':
    unittest.main()
