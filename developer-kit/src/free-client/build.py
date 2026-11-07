#!/usr/bin/env python3
"""Build the helper and version-bound GUI patch from the stock 2.14.1 files.

Writes only build artifacts and manifests. Never changes the original MSI,
installed Editor, personal prefix, native engine or license files.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import argparse
from gui_patch import build_gui_patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MSI_APP = ROOT / 'cache/clean-msi-extract/ProgramFiles64Folder/AI/AIVoice2/AIVoice2Editor'
STOCK_HASH = '10d3493f360ca6a8a8fc6138081b3e79469485197689614c2b2581f772602797'


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--msi-app', type=Path, default=MSI_APP)
    parser.add_argument('--output-dir', type=Path, default=HERE / 'build')
    parser.add_argument('--compiler', type=Path, help='Explicit Roslyn csc.dll; default: installed .NET 8 SDK')
    args = parser.parse_args()
    app = args.msi_app.resolve()
    dll = app / 'AI.Framework.License.dll'
    if sha(dll) != STOCK_HASH:
        raise ValueError('Unsupported license assembly; inspect this version before building')
    compiler = args.compiler
    if compiler is None:
        sdks = subprocess.check_output(['dotnet', '--list-sdks'], text=True).splitlines()
        candidates = []
        for line in sdks:
            version, _, root = line.partition(' [')
            if version.startswith('8.') and root.endswith(']'):
                candidates.append((tuple(int(p) for p in version.split('.')), Path(root[:-1]) / version / 'Roslyn/bincore/csc.dll'))
        if not candidates:
            raise ValueError('Install a .NET 8 SDK for development or pass --compiler csc.dll')
        compiler = max(candidates)[1]
    if not compiler.is_file():
        raise ValueError(f'Compiler not found: {compiler}')
    build = args.output_dir
    build.mkdir(parents=True, exist_ok=True)
    output = build / 'ailm.dll'
    refs = ['System.Private.CoreLib.dll', 'System.Runtime.dll', 'System.Console.dll',
            'System.Linq.dll', 'System.Collections.dll', 'System.Reflection.dll',
            'System.Text.Json.dll', 'System.Memory.dll', 'AI.Framework.License.dll']
    subprocess.run(['dotnet', str(compiler), '-nologo', '-target:exe', '-nostdlib+',
                    '-deterministic+', '-optimize+', '-langversion:10', '-out:' + str(output),
                    *['-reference:' + str(app / name) for name in refs],
                    str(HERE / 'LicenseAdapter.cs')], check=True)
    manifest = {'client': 'A.I.VOICE2 free client', 'editor_version': '2.14.1',
                'adapter_version': '1.0.7-free-client.3', 'sha256': sha(output),
                'requires_original_license_dll_sha256': STOCK_HASH,
                'replaces': 'ailm.dll', 'original_ailm_sha256': sha(app / 'ailm.dll'),
                'source_sha256': sha(HERE / 'LicenseAdapter.cs'),
                'runtime_authentication': 'unchanged', 'personal_activation_required': False,
                'compiler_sha256': sha(compiler)}
    (build / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    gui = build_gui_patch(app / 'data/app.so', build / 'app.so')
    print(output)
    print('SHA-256:', manifest['sha256'])
    print(build / 'app.so')
    print('GUI SHA-256:', gui['sha256'])


if __name__ == '__main__':
    main()
