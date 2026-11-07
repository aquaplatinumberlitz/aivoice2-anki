#!/usr/bin/env python3
"""Compose the preserved installer and a checksum-pinned aivoice2api release."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(archive, output):
    lock = json.loads((ROOT / 'aivoice2api.lock.json').read_text())
    if sha(archive) != lock['artifact_sha256']:
        raise ValueError('Backend archive does not match aivoice2api.lock.json')
    output = output.expanduser().absolute()
    if output.exists():
        raise ValueError('Choose a new output directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.compose-', dir=output.parent) as directory:
        temporary = Path(directory)
        backend = temporary / 'backend'
        backend.mkdir()
        prefix = 'aivoice2api-' + lock['version']
        seen = set()
        with tarfile.open(archive) as tar:
            for member in tar:
                path = PurePosixPath(member.name)
                if (not member.isfile() or path.is_absolute() or '..' in path.parts
                        or not path.parts or path.parts[0] != prefix or path in seen):
                    raise ValueError('Unexpected archive member')
                seen.add(path)
                target = backend.joinpath(*path.parts[1:])
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, target.open('xb') as dest:
                    shutil.copyfileobj(source, dest)
        manifest = json.loads((backend / 'backend-manifest.json').read_text())
        if manifest['source_commit'] != lock['source_commit'] or manifest['version'] != lock['version']:
            raise ValueError('Backend version/commit mismatch')
        actual = {p.relative_to(backend).as_posix() for p in backend.rglob('*') if p.is_file()}
        if actual != set(manifest['files']) | {'backend-manifest.json'}:
            raise ValueError('Unexpected backend file inventory')
        for relative, expected in manifest['files'].items():
            path = backend / relative
            if not path.resolve().is_relative_to(backend) or sha(path) != expected:
                raise ValueError('Backend file hash mismatch: ' + relative)
        stage = temporary / 'setup'
        for name in ['src/setup', 'build/payload', 'release', 'anki']:
            shutil.copytree(ROOT / name, stage / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copy2(ROOT / 'start-setup.sh', stage / 'start-setup.sh')
        shutil.copy2(ROOT / 'aivoice2api.lock.json', stage / 'aivoice2api.lock.json')
        # Keep the original bundle immutable; adapt its two Python call sites here.
        edits = {
            'install_core.py': ("wav,_=engine.speak('こんにちは。',voice_id)",
                                "wav=engine.speak('こんにちは。',voice_id)[0]"),
            'desktop_ui.py': ('output,_=engine.speak(text,voice)', 'output=engine.speak(text,voice)[0]'),
        }
        for name, (old, new) in edits.items():
            path = stage / 'src/setup' / name
            content = path.read_text()
            if content.count(old) != 1:
                raise ValueError('Installer adapter needs review: ' + name)
            path.write_text(content.replace(old, new))
        shutil.copytree(backend / 'runtime', stage / 'src/daemon')
        runtime = stage / 'build/payload/runtime'
        shutil.rmtree(runtime)
        shutil.copytree(backend / 'runtime', runtime)
        shutil.copy2(backend / 'backend-manifest.json', runtime / 'aivoice2api-manifest.json')
        payload = stage / 'build/payload'
        manifest_path = payload / 'payload-manifest.json'
        payload_manifest = json.loads(manifest_path.read_text())
        payload_manifest['backend'] = lock
        payload_manifest['files'] = {p.relative_to(payload).as_posix(): sha(p)
                                     for p in sorted(payload.rglob('*'))
                                     if p.is_file() and p != manifest_path}
        manifest_path.write_text(json.dumps(payload_manifest, indent=2) + '\n')
        (stage / 'README.md').write_text(
            '# Prepared Anki setup\n\nBackend: aivoice2api ' + lock['version'] +
            '.\nRun `bash start-setup.sh` to install into a new managed root.\n'
            'This directory is generated; edit source in the owning repositories.\n'
            'See https://github.com/aquaplatinumberlitz/aivoice2-anki/tree/main/docs\n')
        stage.rename(output)
    print('Prepared setup:', output)
    print('Run: bash ' + repr(str(output / 'start-setup.sh')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.backend_archive, args.output)
