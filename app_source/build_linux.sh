#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
for tool in "$PYTHON_BIN" ffmpeg ffprobe dpkg-deb; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Required build tool is missing: $tool" >&2; exit 2; }
done

VERSION="$($PYTHON_BIN - <<'PY'
import ast, pathlib
p=pathlib.Path('omne_footage_lab.py')
t=ast.parse(p.read_text(encoding='utf-8'))
print(next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='VERSION' for x in n.targets)))
PY
)"

case "$(uname -m)" in
  x86_64|amd64) ARCH_LABEL="x64"; DEB_ARCH="amd64" ;;
  arm64|aarch64) ARCH_LABEL="arm64"; DEB_ARCH="arm64" ;;
  *) echo "Unsupported Linux architecture: $(uname -m)" >&2; exit 2 ;;
esac

APP_NAME="OmN-e Retrospector"
PACKAGE_NAME="omne-retrospector"
INSTALL_ROOT="/usr/lib/$PACKAGE_NAME"

BUILD_VENV="$ROOT/.build-venv"
if [[ ! -x "$BUILD_VENV/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$BUILD_VENV" || {
    echo "Could not create the isolated build environment. On Debian/Ubuntu install python3-venv, then retry." >&2
    exit 2
  }
fi
BUILD_PYTHON="$BUILD_VENV/bin/python"
"$BUILD_PYTHON" -m pip install --upgrade pip
"$BUILD_PYTHON" -m pip install 'pyinstaller>=6.22,<7' 'pillow>=11,<13'

rm -rf build dist dist-linux
mkdir -p dist-linux

"$BUILD_PYTHON" -m PyInstaller --noconfirm --clean --windowed \
  --hidden-import=PIL._tkinter_finder \
  --name "$APP_NAME" \
  --add-binary "$(command -v ffmpeg):tools" \
  --add-binary "$(command -v ffprobe):tools" \
  --add-data "ui_profile.json:." \
  ./omne_footage_lab.py

DIST="$ROOT/dist/$APP_NAME"
[[ -d "$DIST" ]] || { echo "Missing PyInstaller output: $DIST" >&2; exit 1; }

PKGROOT="$ROOT/dist-linux/pkg"
mkdir -p \
  "$PKGROOT$INSTALL_ROOT" \
  "$PKGROOT/usr/bin" \
  "$PKGROOT/usr/share/applications" \
  "$PKGROOT/usr/share/doc/$PACKAGE_NAME" \
  "$PKGROOT/DEBIAN"
cp -a "$DIST/." "$PKGROOT$INSTALL_ROOT/"

cat > "$PKGROOT/usr/bin/omne-retrospector" <<EOF
#!/usr/bin/env sh
exec "$INSTALL_ROOT/$APP_NAME" "\$@"
EOF
chmod 0755 "$PKGROOT/usr/bin/omne-retrospector"

cat > "$PKGROOT/usr/share/applications/omne-retrospector.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=OmN-e Retrospector
Comment=Prepare, transform and preserve footage for OmN-e workflows
Exec=/usr/bin/omne-retrospector
Icon=video-x-generic
Terminal=false
Categories=AudioVideo;Video;Graphics;
StartupNotify=true
EOF

for f in README.txt SYSTEM_REQUIREMENTS.md THIRD_PARTY_NOTICES.txt; do
  [[ ! -f "$f" ]] || cp -p "$f" "$PKGROOT/usr/share/doc/$PACKAGE_NAME/$f"
done

INSTALLED_KIB="$(du -sk "$PKGROOT" | awk '{print $1}')"
cat > "$PKGROOT/DEBIAN/control" <<EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: video
Priority: optional
Architecture: $DEB_ARCH
Maintainer: OmN-e / Pungent Funk <support@omne.space>
Homepage: https://omne.space/
Installed-Size: $INSTALLED_KIB
Description: OmN-e Retrospector audiovisual footage workbench
 A local-first footage preparation, transformation and preview tool for OmN-e.
EOF

cat > "$PKGROOT/DEBIAN/postinst" <<'EOF'
#!/usr/bin/env sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
exit 0
EOF
chmod 0755 "$PKGROOT/DEBIAN/postinst"

cat > "$PKGROOT/DEBIAN/postrm" <<'EOF'
#!/usr/bin/env sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
exit 0
EOF
chmod 0755 "$PKGROOT/DEBIAN/postrm"

DEB="$ROOT/dist-linux/OmN-e_Retrospector_v${VERSION}_Linux_${ARCH_LABEL}.deb"
dpkg-deb --root-owner-group --build "$PKGROOT" "$DEB"
sha256sum "$DEB" > "$DEB.sha256"

echo
echo "Linux package complete:"
echo "  $DEB"
echo "  $DEB.sha256"
echo "Open the .deb in the desktop Software installer for the normal two-click install path."
