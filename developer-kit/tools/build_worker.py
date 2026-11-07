#!/usr/bin/env python3
"""Build the precompiled worker; this is a developer task, never server startup."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'src/daemon/build')
    parser.add_argument('--cc', default='x86_64-w64-mingw32-gcc')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'src/daemon/engine_worker.c'
    output = args.output_dir / 'engine_worker.exe'
    subprocess.run([args.cc, '-Wall', '-Wextra', '-Werror', '-O2',
                    '-Wl,--no-insert-timestamp', str(source), '-o', str(output)], check=True)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {'schema_version': 1, 'worker_protocol': 7,
                'compiler': subprocess.check_output([args.cc, '--version'], text=True).splitlines()[0],
                'files': {p.name: digest(p) for p in [source, source.with_name('engine_api.h')]},
                'worker_sha256': digest(output)}
    (args.output_dir / 'worker-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(output)


if __name__ == '__main__':
    main()
