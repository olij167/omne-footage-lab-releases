# OmN-e Retrospector — Native Build Repository Kit 0.4.0

This repository builds the same Retrospector source natively on Windows and
macOS. PyInstaller is not a cross-compiler.

## One-time bootstrap from the installed owner workspace

```bash
cd ~/.local/share/omne-footage-lab-owner/native_build_repo
./bootstrap_github_repo.sh olij167/omne-footage-lab-releases
```

The script is rerunnable. It creates the public repository if absent, or pushes
the current kit to the existing repository if it already exists.

Then:

```bash
gh workflow run native-release.yml   -R olij167/omne-footage-lab-releases   -f version=0.4.0   -f publish_release=true

gh run watch -R olij167/omne-footage-lab-releases
```

Artifacts:
- Windows x64 Setup EXE + portable ZIP
- macOS Apple Silicon PKG + DMG
- macOS Intel PKG + DMG
- SHA-256 companion for every artifact

Unsigned/ad-hoc builds are suitable for private device testing. Public Windows
distribution should be Authenticode signed. Public macOS distribution should
use Developer ID signing and Apple notarization.

After the GitHub Release passes real-device testing, use the Owner Customiser's
**Sync Native Builds** and **Publish Update…** actions. The large native binaries
remain in immutable GitHub Releases while the trusted omne.space update Worker
proxies only the allow-listed release assets.

See `app_source/SYSTEM_REQUIREMENTS.md` for the CPU/RAM/GPU baseline.

## Native install targets

The release workflow now builds a Linux x64 `.deb` alongside Windows x64 and macOS arm64/x64 packages. The `.deb` is the primary Ubuntu/Zorin install path: download it and open it in the desktop Software installer. The existing `/downloads/footage-lab/*` authority and source ZIP remain compatibility/update infrastructure.
