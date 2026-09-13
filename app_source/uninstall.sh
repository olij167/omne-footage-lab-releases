#!/usr/bin/env bash
set -euo pipefail
# Remove only the public app. Owner workspace, preferences, logs and media stay.
rm -rf -- "$HOME/.local/share/omne-footage-lab"
rm -f -- "$HOME/.local/bin/omne-footage-lab" "$HOME/.local/bin/omne-retrospector" "$HOME/.local/share/applications/omne-footage-lab.desktop" "$HOME/.local/share/applications/omne-retrospector.desktop"
echo "Public application removed. Owner tool, settings, logs and all media were kept."
