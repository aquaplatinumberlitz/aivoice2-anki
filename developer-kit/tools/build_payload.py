#!/usr/bin/env python3
"""Build the installer payload from an explicit stock app; no profile is installed."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = ('server.py', 'run_auth_probe.py', 'runtime_config.py', 'runtime_cli.py', 'voice_registry.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--msi-app', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Build into a new output directory; preserve prior release payloads')
    args.output.mkdir(parents=True)
    subprocess.run([sys.executable, str(ROOT/'tools/build_worker.py'), '--output-dir', str(args.output/'runtime')],check=True)
    subprocess.run([sys.executable, str(ROOT/'src/free-client/build.py'), '--msi-app', str(args.msi_app),
                    '--output-dir', str(args.output/'gui')], check=True)
    for name in RUNTIME_FILES:
        shutil.copy2(ROOT/'src/daemon'/name,args.output/'runtime'/name)
    subprocess.run([sys.executable,str(ROOT/'src/anki-addon/install.py'),'--package-only',
                    '--output',str(args.output/'anki/aivoice2-local.ankiaddon')],check=True)
    # Install payload needs only helper bytes and UI patcher, not another full
    # snapshot copy. The original snapshot is patched after MSI verification.
    (args.output/'gui/app.so').unlink()
    patch_path=args.output/'gui/app.patch.json'
    patch=json.loads(patch_path.read_text())
    patch.update(source='stock-msi/data/app.so',output='app/data/app.so')
    patch_path.write_text(json.dumps(patch,indent=2)+'\n')
    shutil.copy2(ROOT/'src/free-client/gui_patch.py',args.output/'gui/gui_patch.py')
    files={p.relative_to(args.output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(args.output.rglob('*')) if p.is_file()}
    (args.output/'payload-manifest.json').write_text(json.dumps(
        {'schema_version':1,'baseline_id':'aivoice2-2.14.1-company-nv-20261106','files':files},indent=2)+'\n')
    print('PAYLOAD',args.output)


if __name__=='__main__':main()
