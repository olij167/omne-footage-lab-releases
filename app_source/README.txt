OmN-e Footage Lab 0.3.2 — cross-platform desktop application
================================================================

Local video clipping and restrained glitch-art conversion using Python/Tk and
FFmpeg.

Core workflow
-------------
1. Choose the camera/source folder and an output folder.
2. Scan the source folder.
3. Choose Lossless Minimal Clips or a Glitch derivative.
4. Render a short preview when tuning a glitch recipe.
5. Apply to one clip or queue the whole folder.
6. Use Processes / Diagnostics to inspect, retry or repair work.

Lossless mode stream-copies the original encoded streams and splits at keyframes.
It does not reduce bitrate or total library size. The editable 48 MiB default is
an operational working target, not a permanent platform limit.

Glitch mode creates separate H.264 derivatives. Existing recipes, custom recipes,
folder persistence, themes, explanatory tooltips and diagnostics are retained.

Performance / graphics
----------------------
A discrete GPU is NOT required. The processing pipeline is CPU-first and uses
FFmpeg software filters/encoding by default; integrated graphics are sufficient
for the interface. Lossless splitting is light. Motion interpolation and layered
glitch effects can be slower than real time on older CPUs.

See SYSTEM_REQUIREMENTS.md for minimum/recommended specifications.

Interaction model
-----------------
- Mouse wheel scrolls the vertically scrollable area or field under the pointer.
- Shift + wheel targets the field under the pointer first: long single-line
  fields pan horizontally; vertically scrollable editor fields scroll themselves.
- Sliders, spinboxes and comboboxes do not change value merely because the wheel
  passes over them.
- Compact input regions are collapsible and reflow rather than exposing
  horizontal scrollbars.
- The preview never scrolls and always contains the complete frame.

Themes
------
Published themes are selected from Welcome. Users can open Customize… for the
same complete chrome parameter set available to the owner: semantic colours,
fonts, sizing/density, tooltip styling, scrollbars, sliders, status colours and
preview chrome. Personal themes stay local to that device.

Linux/source install
--------------------
On Ubuntu/Zorin:

  sudo apt install -y python3-tk ffmpeg python3-pil.imagetk
  sha256sum -c SHA256SUMS
  bash install.sh
  ~/.local/bin/omne-footage-lab

Pillow provides smooth preview resizing. Older distro Pillow releases are
feature-detected and remain supported by the compatibility fallback.

Windows / macOS
---------------
Native Windows and macOS packages are built from the same source on native
GitHub-hosted runners. FFmpeg/FFprobe are bundled into those applications.
See NATIVE_RELEASE_GUIDE.md.

Updates
-------
Canonical page:
  https://omne.space/downloads/footage-lab/

Manifest:
  https://omne.space/downloads/footage-lab/update.json

The in-app updater validates SHA-256 and only accepts the trusted omne.space
release authority. Large Windows/macOS installers may be proxied by that trusted
Worker from allow-listed immutable GitHub Release assets.

Privacy / ownership
-------------------
Footage Lab is local-first. It does not upload source footage. The public package
does not contain the owner Customiser, publishing credentials, owner logs,
personal conversion presets or source footage.

Diagnostics / history
---------------------
Linux paths:
  ~/.local/state/omne-footage-lab/
  ~/.config/omne-footage-lab/

The corresponding Windows/macOS builds use the platform-native user data
locations.
