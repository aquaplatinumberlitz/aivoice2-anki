#!/usr/bin/env python3
"""Assemble the approved local handover from payload and source allowlists.

No MSI, assets, Wine prefix, collection, cache audio or personal license is
copied. Evidence exports are annotated derivatives; internal originals remain.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.2.0'
CODE_SUFFIXES={'.py','.c','.h','.cs','.js','.json','.md','.sh','.def','.service'}
EVIDENCE_SUFFIXES={'.json','.jsonl','.md','.cs','.txt','.c','.def'}
KEY=re.compile(r'\b(?:[A-Z0-9]{5}-){3}[A-Z0-9]{5}\b')
SAFE_IMAGES={
    'free-client/deactivation-ui/full-patch/patched-license.png',
    'free-client/deactivation-ui/full-patch/patched-restart.png',
    'voice-lifecycle/gui-license-after-remove.png',
    'setup-clean/setup-wizard-complete.png',
    'modern-ui/setup-wizard-complete.png',
    'modern-ui/preview-dialog.png',
}


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def copy_sources(source,destination):
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.is_symlink():continue
        if any(part in ('build','__pycache__') for part in path.relative_to(source).parts):continue
        if path.suffix not in CODE_SUFFIXES:continue
        dest=destination/path.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)


def export_notes(destination):
    provenance=[];omitted=[]
    for path in sorted((ROOT/'notes').rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(ROOT/'notes')
        allowed=path.suffix in EVIDENCE_SUFFIXES
        if path.suffix=='.png':allowed=relative.as_posix().removeprefix('evidence/') in SAFE_IMAGES
        if not allowed:omitted.append(relative.as_posix());continue
        dest=destination/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        if path.suffix=='.png':shutil.copy2(path,dest);continue
        original=path.read_bytes();text=original.decode('utf-8')
        replacements={str(ROOT):'[WORKSPACE]',str(Path.home()):'[AUTHOR_HOME]'}
        for source,target in replacements.items():text=text.replace(source,target)
        # JSON strings and historical Windows paths may contain escaped slashes.
        text=text.replace(str(ROOT).replace('/','\\\\'),'[WORKSPACE]')
        text=KEY.sub('[REDACTED-KEY-LIKE-STRING]',text)
        dest.write_text(text)
        if dest.read_bytes()!=original:
            provenance.append({'path':relative.as_posix(),'original_sha256':hashlib.sha256(original).hexdigest(),
                'export_sha256':sha(dest),'derived_export':True,
                'edits':'author paths and/or key-like strings redacted; not original raw Evidence bytes'})
    (destination/'EXPORT_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (destination/'ARCHIVE_COVERAGE.md').write_text(
        '# Phạm vi archive nghiên cứu\n\nBáo cáo/source và evidence dạng text được giao kèm.\n'
        'Các file liệt kê dưới được giữ ở workspace nội bộ: audio/PCM, binary\n'
        'thử, log thô và ảnh chưa được chọn làm sạch. Không phải file runtime thiếu.\n'
        'Evidence text đã biên tập có mapping/hash trong EXPORT_PROVENANCE.json.\n\n'
        +'\n'.join('- `'+name+'`' for name in omitted)+'\n')
    return provenance,omitted


def repair_archive_links(dev):
    """Archived reports link excluded raw artifacts to the coverage ledger."""
    repairs=[]
    for path in (dev/'notes').rglob('*.md'):
        def replace(match):
            target=match.group(2)
            if '://' in target or target.startswith('#'):return match.group(0)
            plain=target.split('#',1)[0]
            if (path.parent/plain).exists():return match.group(0)
            repairs.append({'report':path.relative_to(dev).as_posix(),'excluded_target':target})
            fallback=os.path.relpath(dev/'notes/ARCHIVE_COVERAGE.md',path.parent)
            return '['+match.group(1)+']('+fallback+')'
        path.write_text(re.sub(r'\[([^\]]+)\]\(([^)]+)\)',replace,path.read_text()))
    (dev/'notes/LINK_EXPORT_MAP.json').write_text(json.dumps(repairs,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--archive',action='store_true')
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists():raise ValueError('Choose a new output directory')
    # Verify before writing the output tree.
    import sys
    sys.path.insert(0,str(ROOT/'src/setup'))
    from install_core import verify_payload
    verify_payload(args.payload)
    output.mkdir(parents=True)
    shutil.copytree(args.payload,output/'build/payload')
    copy_sources(ROOT/'src/setup',output/'src/setup')
    (output/'src/daemon').mkdir(parents=True)
    for name in ['server.py','run_auth_probe.py','runtime_config.py','runtime_cli.py','voice_registry.json']:
        shutil.copy2(ROOT/'src/daemon'/name,output/'src/daemon'/name)
    shutil.copytree(ROOT/'release',output/'release')
    start=output/'start-setup.sh'
    start.write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
        'export PYTHONDONTWRITEBYTECODE=1\n'
        'AIVOICE_BUNDLE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"\n'
        'exec python3 "$AIVOICE_BUNDLE_ROOT/src/setup/manager.py" "$@"\n')
    start.chmod(0o755)
    quick=(ROOT/'docs/START_HERE_VI.md').read_text()
    quick=quick.replace('(DEV_HANDOVER_INDEX_VI.md)','(developer-kit/docs/DEV_HANDOVER_INDEX_VI.md)').replace(
        '(SUPPORT_RUNBOOK_VI.md)','(developer-kit/docs/SUPPORT_RUNBOOK_VI.md)')
    (output/'START_HERE_VI.md').write_text(quick)
    shutil.copy2(ROOT/'CHANGELOG.md',output/'CHANGELOG.md')
    shutil.copytree(args.payload/'anki',output/'anki')
    dev=output/'developer-kit';dev.mkdir()
    for name in ['src','tools','tests']:copy_sources(ROOT/name,dev/name)
    shutil.copytree(ROOT/'docs',dev/'docs');shutil.copytree(ROOT/'release',dev/'release')
    shutil.copy2(ROOT/'README.md',dev/'WORKSPACE_README.md')
    if (ROOT/'PLAN.md').is_file():shutil.copy2(ROOT/'PLAN.md',dev/'PLAN.md')
    else:(dev/'PLAN.md').write_text('# Historical PoC plan\n\nKhông có file plan lịch sử trong source snapshot này. '
                                  'Kế hoạch hiện hành: [DELIVERY_PLAN_VI.md](docs/DELIVERY_PLAN_VI.md).\n')
    (dev/'README.md').write_text('# Dev-kit cùng phiên bản runtime\n\n'
        'Đọc [chỉ mục dev](docs/DEV_HANDOVER_INDEX_VI.md), [build](docs/BUILD_AND_REPRODUCE_VI.md), '
        '[runbook](docs/SUPPORT_RUNBOOK_VI.md).\n\n'
        'WORKSPACE_README.md và PLAN.md mô tả nghiên cứu cũ; không phải bố trí cài của khách.\n'
        'Source/tool nghiên cứu trong src/research không được tự cài vào runtime.\n')
    edits,omitted=export_notes(dev/'notes')
    repair_archive_links(dev)
    # Link rewrites also create derived bytes; compute provenance after edits.
    edits=[]
    for path in sorted((dev/'notes').rglob('*')):
        original=ROOT/'notes'/path.relative_to(dev/'notes')
        if path.is_file() and original.is_file() and sha(path)!=sha(original):
            edits.append({'path':path.relative_to(dev/'notes').as_posix(),'original_sha256':sha(original),
                          'export_sha256':sha(path),'derived_export':True,
                          'edits':'author-path/key-like-string redaction and/or archive-link rewrite'})
    (dev/'notes/EXPORT_PROVENANCE.json').write_text(json.dumps(edits,indent=2)+'\n')
    # Annotate every copied RE report, including those whose export links changed.
    (dev/'notes/EXPORT_README.md').write_text('# Evidence/report export\n\n'
        'Đây là archive hỗ trợ dev đã chọn/làm sạch. Các Evidence ID/hash binary\n'
        'tham chiếu quan sát gốc; export đã biên tập không phải raw capture/snapshot\n'
        'nguyên bản để replay. Xem EXPORT_PROVENANCE.json và LINK_EXPORT_MAP.json.\n'
        'Dùng baseline và input stock riêng để tái điều tra khi cần.\n')
    files={p.relative_to(output).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}
           for p in sorted(output.rglob('*')) if p.is_file()}
    acceptance=json.loads((ROOT/'release/user-acceptance.json').read_text())
    manifest={'schema_version':1,'version':VERSION,'status':acceptance['status'],
        'external_inputs':['Original MSI 2.14.1','Company-supplied Lang/voicebanks'],
        'files':files,'derived_evidence_exports':len(edits),'omitted_research_artifacts':len(omitted),
        'user_acceptance':acceptance,
        'known_limits':['Full update/uninstall not included in this handover',
            'Full power-loss matrix not qualified', 'Windows native/other distributions not certified'],
        'vntext':'roadmap only; deferred until Anki pipeline completion'}
    (output/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    checks={p.relative_to(output).as_posix():sha(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output/'SHA256SUMS').write_text(''.join(digest+'  '+name+'\n' for name,digest in checks.items()))
    if args.archive:
        archive=output.parent/(output.name+'.tar.gz')
        if archive.exists():raise ValueError('Archive already exists')
        def normalize(info):
            info.uid=info.gid=0;info.uname=info.gname='';info.mtime=1793923200;return info
        with tarfile.open(archive,'w:gz') as bundle:bundle.add(output,arcname=output.name,filter=normalize)
        print('ARCHIVE',archive)
    print('HANDOVER',output)
    print('FILES',len(checks))


if __name__=='__main__':main()
