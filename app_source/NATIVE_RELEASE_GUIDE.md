# OmN-e Footage Lab — Windows + macOS release guide

The desktop runtime is shared Python/Tk + FFmpeg code, but native packages must be built on their target operating system. PyInstaller is not a cross-compiler.

## Supported release targets

- Linux/source ZIP — built and published by the owner Customiser.
- Windows x64 Setup EXE — built on Windows.
- macOS Apple Silicon PKG/DMG — built on an arm64 Mac runner.
- macOS Intel PKG/DMG — built on an Intel Mac runner.

The in-app updater selects an architecture-specific package from `update.json`.

## Recommended automated build

Use the separate Native Build Repository Kit. Its GitHub Actions workflow runs on Windows and both macOS architectures, publishes immutable native binaries to a public GitHub Release, and produces SHA-256 companions.

After a GitHub Release is ready, the owner machine syncs its metadata:

```bash
python3 ~/.local/share/omne-footage-lab-owner/owner/sync_native_release.py \
  --repo OWNER/REPOSITORY \
  --version 0.3.2 \
  --web ~/.local/share/omne-footage-lab-owner/web
```

Then the ordinary owner **Publish Update…** process builds the Linux/source ZIP, adds the native platform metadata, and deploys the cross-platform manifest through omne.space.

## Why native installers are not Workers Static Assets

Workers Static Assets have a 25 MiB per-file limit. Self-contained desktop packages with FFmpeg are expected to exceed it. Native packages therefore live on public GitHub Releases while the update Worker proxies allow-listed binaries through `https://omne.space/downloads/footage-lab/files/...`.

## macOS signing

Private tests can use PyInstaller's ad-hoc signing. A polished public macOS release should use Apple-issued Developer ID Application and Developer ID Installer certificates, hardened runtime, and Apple notarization. The build script supports `notarytool` when the appropriate environment variables are supplied.

## Windows signing

Unsigned builds are usable for testing but may trigger SmartScreen warnings. The Windows script can Authenticode-sign the Setup EXE when an imported signing certificate thumbprint is supplied through `OMNE_WINDOWS_CERT_THUMBPRINT`.

## Owner-workspace bootstrap

The native repository template is already installed with the owner workspace.
You do not need to keep a separately extracted Downloads copy:

```bash
cd ~/.local/share/omne-footage-lab-owner/native_build_repo
./bootstrap_github_repo.sh OWNER/REPOSITORY
```

The Owner Customiser also exposes **Create Native Repo**, which runs the same
idempotent bootstrap and can safely update an existing repository.
