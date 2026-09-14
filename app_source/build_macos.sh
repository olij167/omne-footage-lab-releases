#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 is required." >&2
  exit 2
fi
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "FFmpeg and FFprobe are required. On macOS with Homebrew: brew install ffmpeg" >&2
  exit 2
fi

VERSION="$($PYTHON_BIN - <<'PY'
import ast, pathlib
p=pathlib.Path('omne_footage_lab.py')
t=ast.parse(p.read_text(encoding='utf-8'))
print(next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='VERSION' for x in n.targets)))
PY
)"

MACHINE="$(uname -m)"
case "$MACHINE" in
  arm64|aarch64) ARCH_LABEL="arm64" ;;
  x86_64|amd64) ARCH_LABEL="x64" ;;
  *) echo "Unsupported macOS architecture: $MACHINE" >&2; exit 2 ;;
esac

APP_NAME="OmN-e Retrospector"
BUNDLE_ID="${OMNE_MACOS_BUNDLE_ID:-space.omne.footagelab}"
APP_IDENTITY="${OMNE_MACOS_APPLICATION_IDENTITY:-}"
INSTALLER_IDENTITY="${OMNE_MACOS_INSTALLER_IDENTITY:-}"
ENTITLEMENTS="${OMNE_MACOS_ENTITLEMENTS:-$ROOT/macos_entitlements.plist}"

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install 'pyinstaller>=6.22,<7' 'pillow>=11,<13'

rm -rf build dist dist-macos
mkdir -p dist-macos

PYI_ARGS=(
  --noconfirm --clean --windowed
  --hidden-import=PIL._tkinter_finder
  --name "$APP_NAME"
  --osx-bundle-identifier "$BUNDLE_ID"
  --add-binary "$(command -v ffmpeg):tools"
  --add-binary "$(command -v ffprobe):tools"
  --add-data "ui_profile.json:."
)

if [[ -n "$APP_IDENTITY" ]]; then
  PYI_ARGS+=(--codesign-identity "$APP_IDENTITY")
  if [[ -f "$ENTITLEMENTS" ]]; then
    PYI_ARGS+=(--osx-entitlements-file "$ENTITLEMENTS")
  fi
fi

"$PYTHON_BIN" -m PyInstaller "${PYI_ARGS[@]}" ./omne_footage_lab.py

APP_PATH="$ROOT/dist/$APP_NAME.app"
[[ -d "$APP_PATH" ]] || { echo "Missing app bundle: $APP_PATH" >&2; exit 1; }

# Keep human-readable release documentation beside the application in the DMG.
DOCS_DIR="$ROOT/dist-macos/Documentation"
mkdir -p "$DOCS_DIR"
for f in README.txt QA_REPORT.txt RELEASE_GUIDE.md SYSTEM_REQUIREMENTS.md THIRD_PARTY_NOTICES.txt; do
  [[ ! -f "$f" ]] || cp -p "$f" "$DOCS_DIR/$f"
done

PKG_UNSIGNED="$ROOT/dist-macos/OmN-e_Retrospector_v${VERSION}_macOS_${ARCH_LABEL}_unsigned.pkg"
PKG_FINAL="$ROOT/dist-macos/OmN-e_Retrospector_v${VERSION}_macOS_${ARCH_LABEL}.pkg"

pkgbuild \
  --component "$APP_PATH" \
  --install-location "/Applications" \
  "$PKG_UNSIGNED"

if [[ -n "$INSTALLER_IDENTITY" ]]; then
  productsign --sign "$INSTALLER_IDENTITY" "$PKG_UNSIGNED" "$PKG_FINAL"
  rm -f "$PKG_UNSIGNED"
else
  mv "$PKG_UNSIGNED" "$PKG_FINAL"
fi

DMG_STAGE="$ROOT/dist-macos/dmg-root"
rm -rf "$DMG_STAGE"
mkdir -p "$DMG_STAGE"
cp -R "$APP_PATH" "$DMG_STAGE/"
cp -R "$DOCS_DIR" "$DMG_STAGE/"
ln -s /Applications "$DMG_STAGE/Applications"
DMG_FINAL="$ROOT/dist-macos/OmN-e_Retrospector_v${VERSION}_macOS_${ARCH_LABEL}.dmg"
hdiutil create -volname "$APP_NAME $VERSION" -srcfolder "$DMG_STAGE" -ov -format UDZO "$DMG_FINAL" >/dev/null
rm -rf "$DMG_STAGE"

# Optional notarization. For CI/local release use an app-specific password.
# Required environment variables:
#   OMNE_APPLE_ID, OMNE_APPLE_TEAM_ID, OMNE_APPLE_APP_PASSWORD
if [[ -n "${OMNE_APPLE_ID:-}" && -n "${OMNE_APPLE_TEAM_ID:-}" && -n "${OMNE_APPLE_APP_PASSWORD:-}" ]]; then
  if [[ -z "$APP_IDENTITY" || -z "$INSTALLER_IDENTITY" ]]; then
    echo "Notarization credentials are set, but Developer ID app/installer identities are missing." >&2
    exit 2
  fi
  xcrun notarytool submit "$PKG_FINAL" \
    --apple-id "$OMNE_APPLE_ID" \
    --team-id "$OMNE_APPLE_TEAM_ID" \
    --password "$OMNE_APPLE_APP_PASSWORD" \
    --wait
  xcrun stapler staple "$PKG_FINAL"

  xcrun notarytool submit "$DMG_FINAL" \
    --apple-id "$OMNE_APPLE_ID" \
    --team-id "$OMNE_APPLE_TEAM_ID" \
    --password "$OMNE_APPLE_APP_PASSWORD" \
    --wait
  xcrun stapler staple "$DMG_FINAL"
fi

for artifact in "$PKG_FINAL" "$DMG_FINAL"; do
  shasum -a 256 "$artifact" > "${artifact}.sha256"
done

# Smoke-test bundle metadata and code signature. Ad-hoc signing is acceptable for
# private testing; public distribution should use Developer ID + notarization.
/usr/bin/codesign --verify --deep --strict "$APP_PATH"
/usr/bin/plutil -p "$APP_PATH/Contents/Info.plist" >/dev/null

echo
echo "macOS build complete ($ARCH_LABEL):"
echo "  $PKG_FINAL"
echo "  $DMG_FINAL"
if [[ -z "$APP_IDENTITY" ]]; then
  echo "  NOTE: ad-hoc signed test build. Use Developer ID + notarization for public distribution."
else
  echo "  Developer ID application signing requested."
fi
