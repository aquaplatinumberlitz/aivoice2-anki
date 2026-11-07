#!/usr/bin/env python3
"""Inventory and package the current installer; never builds a backend fork."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/setup'))
from install_core import verify_payload


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    # Use the index in a checkout; handover recipients do not need Git installed.
    checkout = None
    if shutil.which('git'):
        checkout = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--show-toplevel'],
                                  capture_output=True, text=True)
    if checkout and checkout.returncode == 0 and Path(checkout.stdout.strip()) == ROOT:
        names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z',
                                         '--cached', '--others', '--exclude-standard']).split(b'\0')
        paths = [ROOT / name.decode() for name in names if name]
    else:
        excluded = {'.git', '__pycache__', '.venv', 'venv', 'dist', 'cache', 'logs', 'prefixes', 'wineprefix'}
        paths = [p for p in ROOT.rglob('*') if not excluded.intersection(p.relative_to(ROOT).parts)
                 and not (p.relative_to(ROOT).parts[0] == 'build' and
                          any(part.startswith(('setup-', 'backend-download')) for part in p.relative_to(ROOT).parts[1:]))]
    return sorted({p.relative_to(ROOT).as_posix() for p in paths if p.is_file()
                   and p.relative_to(ROOT).as_posix() not in ('SHA256SUMS', 'release-manifest.json')})


def refresh():
    payload = ROOT / 'build/payload'
    manifest_path = payload / 'payload-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['backend'] = json.loads((ROOT / 'aivoice2api.lock.json').read_text())
    manifest['files'] = {p.relative_to(payload).as_posix(): sha(p)
                         for p in sorted(payload.rglob('*')) if p.is_file() and p != manifest_path
                         and '__pycache__' not in p.parts}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    verify_payload(payload)
    release = {'schema_version': 1, 'version': (ROOT / 'VERSION').read_text().strip(),
               'status': 'backend-upgraded', 'backend': manifest['backend'],
               'external_inputs': ['Original MSI 2.14.1', 'Company-supplied Lang/voicebanks'],
               'scope': 'Pinned backend and installer checks; no new independent-machine or speaker QA claim',
               'files': {name: {'bytes': (ROOT / name).stat().st_size, 'sha256': sha(ROOT / name)}
                         for name in inventory()}}
    release_path = ROOT / 'release-manifest.json'
    release_path.write_text(json.dumps(release, ensure_ascii=False, indent=2) + '\n')
    records = {name: record['sha256'] for name, record in release['files'].items()}
    records['release-manifest.json'] = sha(release_path)
    (ROOT / 'SHA256SUMS').write_text(''.join(digest + '  ' + name + '\n'
                                            for name, digest in sorted(records.items())))
    return release


def check():
    verify_payload(ROOT / 'build/payload')
    release = json.loads((ROOT / 'release-manifest.json').read_text())
    if set(release['files']) != set(inventory()):
        raise ValueError('Release inventory changed; run --refresh')
    for name, record in release['files'].items():
        if sha(ROOT / name) != record['sha256']:
            raise ValueError('Release file hash mismatch: ' + name)
    subprocess.run(['sha256sum', '--quiet', '-c', 'SHA256SUMS'], cwd=ROOT, check=True)
    return release


def package(output, release):
    output.mkdir(parents=True, exist_ok=True)
    name = 'aivoice2-anki-' + release['version']
    archive = output / (name + '.tar.gz')
    if archive.exists():
        raise ValueError('Archive already exists; choose a new output directory')
    with archive.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for relative in sorted([*release['files'], 'release-manifest.json', 'SHA256SUMS']):
            source = ROOT / relative
            if source.is_symlink():
                raise ValueError('Symlinks are not release inputs: ' + relative)
            data = source.read_bytes()
            info = tarfile.TarInfo(name + '/' + relative)
            info.size = len(data)
            info.mode = 0o755 if relative.endswith('.sh') else 0o644
            tar.addfile(info, io.BytesIO(data))
    archive.with_name(archive.name + '.sha256').write_text(sha(archive) + '  ' + archive.name + '\n')
    print('Archive:', archive)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Record deliberate release input changes')
    parser.add_argument('--output', type=Path, help='Create a handover archive in this directory')
    args = parser.parse_args()
    release = refresh() if args.refresh else check()
    if args.output:
        package(args.output, release)
    print('Release:', release['version'], 'backend:', release['backend']['version'], 'verified')
