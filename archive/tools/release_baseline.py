#!/usr/bin/env python3
"""Inventory explicit MSI/extracted-stock/company-assets; never collect a home/prefix.

Source roots stay in command arguments. The portable manifest contains only
relative source paths and hashes, never license contents or machine identity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MSI_SHA256 = '81a5d80ada94d6646373b9ab54dcfe4ddd824c45a66c7f071648a54838c92d90'
STOCK_HASHES = {
    'AI.Framework.License.dll': '10d3493f360ca6a8a8fc6138081b3e79469485197689614c2b2581f772602797',
    'data/app.so': '1cecf26ccecf3d6e89a6ae7a0962284fbe242cfffe3959f6a9eb052e432d5db6',
    'Lib/AITalk/aitalk_engine.dll': '711aa449c58754bd89402093e077695e8e6175159623c8cf063b979aa3515c17',
    'Lib/AITalk/aitalk.lic': 'c7a013e6dabbc143b1fe5352ad38b5f9bd117b7b22abe46911c21b49bfe7004b',
}
COMPANY_VOICES = ('KotonohaAkane_ns_48', 'KotonohaAoi_ns_48',
                  'MeikaHime_ns_48', 'MeikaMikoto_ns_48')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(root, source_id):
    result = []
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f'Missing or symlinked source directory: {root}')
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Refusing symlink in release input: {path}')
        if path.is_file():
            result.append({'source': source_id, 'path': path.relative_to(root).as_posix(),
                           'bytes': path.stat().st_size, 'sha256': sha(path)})
    return result


def create_baseline(msi, app, assets):
    if sha(msi) != MSI_SHA256:
        raise ValueError('MSI differs from the inspected 2.14.1 input')
    stock = inventory(app, 'msi-extracted-app')
    by_path = {item['path']: item['sha256'] for item in stock}
    for relative, expected in STOCK_HASHES.items():
        if by_path.get(relative) != expected:
            raise ValueError(f'Not the inspected stock file: {relative}')
    languages = inventory(assets / 'Lang', 'company-language')
    voice_files = []
    for name in COMPANY_VOICES:
        files = inventory(assets / 'voicebanks' / name, 'company-voicebanks')
        for item in files:
            item['path'] = name + '/' + item['path']
        required = {name + '/' + file for file in [name + '.aivdic', 'voice.lic', 'infox.bin', 'images.dat']}
        if not required.issubset({item['path'] for item in files}):
            raise ValueError(f'Incomplete GUI voicebank: {name}')
        voice_files.extend(files)
    # Compare the license/dictionary inputs to the previously recorded clean
    # execution. GUI artwork/metadata are inventoried but not claimed PCM inputs.
    evidence = ROOT / 'notes/evidence/clean-runtime/company-assets/manifest.json'
    clean = json.loads(evidence.read_text())
    expected = {r['path']: r['sha256'] for r in clean if r['path'].startswith(('Lang/', 'Voice/'))}
    observed = {'Lang/' + r['path']: r['sha256'] for r in languages}
    observed.update({'Voice/' + r['path']: r['sha256'] for r in voice_files})
    for relative, expected_sha in expected.items():
        if observed.get(relative) != expected_sha:
            raise ValueError(f'Company asset differs from clean-run evidence: {relative}')
    registry = json.loads((ROOT / 'src/daemon/voice_registry.json').read_text())['voices']
    return {
        'schema_version': 1, 'baseline_id': 'aivoice2-2.14.1-company-nv-20261106',
        'editor_version': '2.14.1', 'platform_target': 'linux-x86_64-wine',
        'scope': 'Input baseline; not a signed or fully qualified customer release',
        'sources': {'original-msi': {'filename': msi.name, 'bytes': msi.stat().st_size,
                                     'sha256': MSI_SHA256},
                    'msi-extracted-app': {'origin': 'original-msi'},
                    'company-language': {'origin': 'separately-supplied Lang directory'},
                    'company-voicebanks': {'origin': 'separately-supplied voicebanks directory'}},
        'supported_voice_candidates': [{'folder': name, 'language': registry[name]['language']}
                                       for name in COMPANY_VOICES],
        'excluded_from_distribution': 'Legacy/galaco installed-assets research; personal prefixes/activation; sidecar patched framework DLLs',
        'files': stock + languages + voice_files,
        'evidence': ['notes/evidence/clean-runtime/company-assets/result.json',
                     'notes/evidence/free-client/deactivation-ui/result.json',
                     'notes/evidence/free-client/msi-lang-inventory/result.json'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--msi', type=Path, required=True)
    parser.add_argument('--msi-app', type=Path, required=True)
    parser.add_argument('--assets-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'release/release-inputs.json')
    args = parser.parse_args()
    result = create_baseline(args.msi, args.msi_app, args.assets_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f'Baseline: {len(result["files"])} files, {len(COMPANY_VOICES)} company voice candidates')
    print(args.output)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(f'Baseline failed: {error}', file=sys.stderr)
        sys.exit(1)
