#!/usr/bin/env python3
"""Install this addon locally and build an .ankiaddon archive."""
import json
import argparse
from pathlib import Path
import shutil
import zipfile

SOURCE = Path(__file__).resolve().parent
FILES = ('__init__.py', 'card_model.py', 'editor_compat.py', 'selection.js', 'config.json', 'config.md', 'manifest.json')
TARGET = Path.home() / '.local/share/Anki2/addons21/aivoice2_local'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-only', action='store_true', help='Build without writing any Anki profile/addon')
    parser.add_argument('--target', type=Path, default=TARGET, help='Explicit addon directory when installing locally')
    parser.add_argument('--output', type=Path, default=SOURCE.parents[1] / 'cache/aivoice2-local.ankiaddon')
    args = parser.parse_args()
    if not args.package_only:
        target = args.target.expanduser()
        target.mkdir(parents=True, exist_ok=True)
        for filename in FILES:
            shutil.copy2(SOURCE / filename, target / filename)
        meta_path = target / 'meta.json'
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        meta['name'] = 'A.I.VOICE2 Local TTS'
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print(f'Installed: {target}\nRestart Anki to load addon changes.')
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for filename in FILES:
            info = zipfile.ZipInfo(filename, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (SOURCE / filename).read_bytes())
    print(f'Package: {output}')
