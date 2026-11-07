#!/usr/bin/env python3
"""Verify all release checksums and the absence of personal/runtime data files."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('bundle',type=Path)
    args=parser.parse_args();root=args.bundle.resolve();checked=0
    lines=(root/'SHA256SUMS').read_text().splitlines();listed=set()
    for line in lines:
        expected,relative=line.split('  ',1);path=root/relative
        assert len(expected)==64 and path.resolve().is_relative_to(root),relative
        assert path.is_file() and not path.is_symlink(),relative
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        assert actual==expected,relative
        listed.add(relative);checked+=1
    actual_files={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual_files==listed|{'SHA256SUMS'},'Unlisted or missing bundle files'
    denied={'.lic','.reg','.anki2','.wav','.pcm','.msi','.aivdic','.aildic'}
    forbidden=[name for name in actual_files if Path(name).suffix.lower() in denied]
    assert not forbidden,forbidden
    assert not any(part in ('wineprefix','__pycache__','collection.media')
                   for name in actual_files for part in Path(name).parts)
    result={'passed':True,'files_verified':checked,'contains_original_msi_or_voice_data':False,
            'scope':'Checksum/allowlist verification; not full software or independent-machine QA'}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
