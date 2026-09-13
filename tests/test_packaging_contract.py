import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackagingContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def test_release_files_include_new_runtime_modules_and_linux_builder(self):
        doc = json.loads(self.read('app_source/release_files.json'))
        files = set(doc['files'])
        for required in {'builtin_themes.py','theme_color_math.py','theme_interchange.py','preview_view.py','build_linux.sh'}:
            self.assertIn(required, files)

    def test_source_installer_uses_retrospector_launcher_and_desktop_but_keeps_technical_storage(self):
        text = self.read('app_source/install.sh')
        self.assertIn("target=Path.home()/'.local/share/omne-footage-lab'", text)
        self.assertIn("launcher=bins/'omne-retrospector'", text)
        self.assertIn("compat_launcher=bins/'omne-footage-lab'", text)
        self.assertIn('applications/omne-retrospector.desktop', text)
        self.assertIn('applications/omne-footage-lab.desktop', text)
        self.assertIn('unlink(missing_ok=True)', text)

    def test_windows_installer_is_retrospector_but_keeps_upgrade_appid(self):
        text = self.read('app_source/windows_installer.iss')
        self.assertIn('#define MyAppName "OmN-e Retrospector"', text)
        self.assertIn('AppId={{D4423B8B-E250-4B30-B516-0DDBFCF09DA0}', text)
        self.assertIn(r'DefaultDirName={localappdata}\Programs\OmN-e Retrospector', text)
        self.assertIn('Launch OmN-e Retrospector', text)
        self.assertIn('OmN-e_Retrospector_v{#MyAppVersion}_Windows_{#MyAppArch}_Setup', text)
        # Same AppId + Inno's default UsePreviousAppDir means upgrades retain an
        # existing legacy install directory while fresh installs use Retrospector.
        self.assertNotIn('DefaultDirName={localappdata}\\Programs\\OmN-e Footage Lab', text)

    def test_native_builds_use_retrospector_artifact_names_and_stable_bundle_id(self):
        windows = self.read('app_source/build_windows.ps1')
        mac = self.read('app_source/build_macos.sh')
        linux = self.read('app_source/build_linux.sh')
        self.assertIn('$AppName = "OmN-e Retrospector"', windows)
        self.assertIn('OmN-e_Retrospector_v${Version}_Windows_${ArchLabel}_Portable.zip', windows)
        self.assertIn('APP_NAME="OmN-e Retrospector"', mac)
        self.assertIn('space.omne.footagelab', mac)
        self.assertIn('OmN-e_Retrospector_v${VERSION}_macOS_${ARCH_LABEL}.pkg', mac)
        self.assertIn('PACKAGE_NAME="omne-retrospector"', linux)
        self.assertIn('OmN-e_Retrospector_v${VERSION}_Linux_${ARCH_LABEL}.deb', linux)
        self.assertIn('.build-venv', linux)
        self.assertIn('-m venv', linux)

    def test_github_workflow_builds_linux_and_keeps_compatibility_backend(self):
        workflow = self.read('.github/workflows/native-release.yml')
        self.assertIn('Build native OmN-e Retrospector release', workflow)
        self.assertIn('linux-x64:', workflow)
        self.assertIn('OmN-e_Retrospector_v${{ needs.validate.outputs.version }}_Linux_x64.deb', workflow)
        self.assertIn('https://omne.space/downloads/footage-lab/', workflow)
        self.assertIn('python -m unittest discover -s tests -v', workflow)


if __name__ == '__main__':
    unittest.main()
