#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 - <<'PY'
import sys, tkinter
if sys.version_info < (3,10):raise SystemExit('Python 3.10+ is required.')
PY
for tool in ffmpeg ffprobe; do
  command -v "$tool" >/dev/null || { printf '%s is missing. Install ffmpeg with your package manager.\n' "$tool" >&2; exit 2; }
done
python3 - "$HERE" <<'PY'
from pathlib import Path
import json, os, shutil, sys, time, uuid
source=Path(sys.argv[1]); target=Path.home()/'.local/share/omne-footage-lab'
manifest=json.loads((source/'release_files.json').read_text(encoding='utf-8'))
names=manifest['files']; target.mkdir(parents=True,exist_ok=True)
backup=Path.home()/'.local/state/omne-footage-lab/install_backups'/(time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6])
for name in names:
    rel=Path(name)
    if rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name:raise SystemExit('Unsafe install path')
    p=source/rel;dest=target/rel
    if p.is_symlink() or not p.is_file():raise SystemExit('Missing or symlinked release file: '+name)
    if not dest.resolve().is_relative_to(target.resolve()):raise SystemExit('Unsafe destination')
    if p.suffix=='.py':compile(p.read_text(encoding='utf-8'),str(p),'exec')
for name in names:
    src=source/name;dest=target/name
    if src.resolve()==dest.resolve():continue
    if dest.exists():
        b=backup/name;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,b)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    dest.chmod(0o755 if dest.suffix in {'.py','.sh'} else 0o644)
bins=Path.home()/'.local/bin';bins.mkdir(parents=True,exist_ok=True)
launcher=bins/'omne-retrospector';compat_launcher=bins/'omne-footage-lab'
import shlex
launcher.write_text('#!/usr/bin/env bash\nexec python3 '+shlex.quote(str(target/'omne_footage_lab.py'))+' "$@"\n');launcher.chmod(0o755)
compat_launcher.write_text('#!/usr/bin/env bash\nexec '+shlex.quote(str(launcher))+' "$@"\n');compat_launcher.chmod(0o755)
profile=json.loads((target/'ui_profile.json').read_text(encoding='utf-8'))
name=str(profile.get('identity',{}).get('app_name','OmN-e Retrospector')).replace('\n',' ').replace('\r',' ')
desktop=Path.home()/'.local/share/applications/omne-retrospector.desktop';desktop.parent.mkdir(parents=True,exist_ok=True)
legacy_desktop=Path.home()/'.local/share/applications/omne-footage-lab.desktop'
quoted='"'+str(launcher).replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'
desktop.write_text('[Desktop Entry]\nType=Application\nName='+name+'\nComment=Clip footage and render glitch-art recipes\nExec='+quoted+'\nIcon=video-x-generic\nTerminal=false\nCategories=AudioVideo;Utility;\nStartupNotify=true\n')
legacy_desktop.unlink(missing_ok=True)
print('Installed public application:',launcher)
print('User folders, presets, logs and media were not removed.')
try:
    from PIL import Image,ImageTk
    print('Preview/theme tools: smooth Pillow preview, colour wheel and desktop eyedropper enabled.')
except ImportError:
    print('Preview/theme tools: Tk fallback active. For smooth preview + colour wheel + desktop eyedropper: sudo apt install python3-pil.imagetk')
PY
