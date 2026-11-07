#!/usr/bin/env python3
"""Version-bound free-client UI patch for the original 2.14.1 Dart snapshot.

Hide the deactivation instruction/button, retain the voicebank cards, and
neutralize only the button's onPressed closure. No native engine/auth changes.
"""
import hashlib
import json
from pathlib import Path

ORIGINAL_SHA256 = '1cecf26ccecf3d6e89a6ae7a0962284fbe242cfffe3959f6a9eb052e432d5db6'
PATCH_VERSION = '2.14.1-free-ui.1'

# DeactivateLicense.build constructs a Column with instruction, spacer,
# deactivate button, and LicenseCardList. Keep the fourth child unchanged.
# PP+0x723f is the existing const SizedBox.shrink (width=height=0) in this build.
PATCHES = (
    {
        'name': 'hide-deactivation-instructions-and-button',
        'offset': 0x9E515D,
        'before': '488b45d048894df0488941174d8b9fa7a402004c89591f488b45e848894127',
        'after': ('48894df0'              # preserve array in the frame
                  '498b873f720000'        # rax = existing SizedBox.shrink
                  '48894117'              # replace instruction widget
                  '4889411f'              # replace spacer
                  '48894127'              # replace deactivate button
                  '9090909090909090'),    # retain exact code size
    },
    {
        'name': 'neutralize-deactivate-onpressed-closure',
        'offset': 0x9E52B0,
        'before': '554889e54883ec18',
        'after': '498b86d0000000c3',        # Dart null in rax; return, no dialog/call
    },
)


def build_gui_patch(source: Path, output: Path):
    original = source.read_bytes()
    actual = hashlib.sha256(original).hexdigest()
    if actual != ORIGINAL_SHA256:
        raise ValueError(f'Unsupported GUI snapshot: {actual}; expected stock 2.14.1')
    data = bytearray(original)
    observations = []
    for patch in PATCHES:
        start = patch['offset']
        before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        if len(before) != len(after) or data[start:start + len(before)] != before:
            raise ValueError(f'Patch precondition failed: {patch["name"]}')
        data[start:start + len(after)] = after
        observations.append({**patch, 'offset': hex(start), 'bytes': len(after)})
    if source.resolve() == output.resolve():
        raise ValueError('Write to a separate output; preserve the original snapshot')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    manifest = {
        'patch_version': PATCH_VERSION,
        'original_sha256': actual,
        'sha256': hashlib.sha256(data).hexdigest(),
        'source': str(source),
        'output': str(output),
        'patches': observations,
        'voicebank_list': 'preserved',
        'native_engine_authentication': 'unchanged',
    }
    output.with_suffix('.patch.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build_gui_patch(args.source, args.output), indent=2))
