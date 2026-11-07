"""Add/remove/restore known voicebanks in one managed app/Voice directory."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import uuid

from install_core import atomic_json, commit_directory, safe_file, sha, verified_files
from runtime_config import load_config,load_voice_registry
from voice_sources import prepare_voice_import


def managed_config(root):
    root=Path(root).resolve()
    manifest=json.loads((root/'install-manifest.json').read_text())
    if manifest.get('schema_version')!=1:raise ValueError('Không phải bản cài được quản lý')
    config=load_config(root/'config/runtime.json')
    if config.app_dir!=root/'app':raise ValueError('app_dir không thuộc bản cài đang quản lý')
    return root,config,manifest


def foreign_running_processes(config):
    matches=[]
    prefixes={str(config.gui_prefix),str(config.engine_prefix)}
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            env=dict(part.split(b'=',1) for part in (proc/'environ').read_bytes().split(b'\0') if b'=' in part)
            prefix=env.get(b'WINEPREFIX',b'').decode(errors='replace')
            command=(proc/'cmdline').read_bytes().lower()
            if prefix in prefixes and any(name in command for name in [b'aivoice.exe',b'engine_worker.exe']):
                matches.append(int(proc.name))
        except (OSError,ValueError):continue
    return matches


@contextmanager
def maintenance(root,config):
    lease=(root/'.runtime.lock').open('a+b')
    try:
        try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Đóng Editor và dừng backend của bản cài này trước khi quản lý giọng.')
        if foreign_running_processes(config):
            raise ValueError('Còn Editor/worker đang chạy trong prefix. Lưu và đóng trước khi thay giọng.')
        yield
    finally:lease.close()


def refresh_manifest(root,manifest,selected):
    config_path=root/'config/runtime.json'
    data=json.loads(config_path.read_text())
    available=sorted(selected)
    if data.get('default_voice','').split('/')[0] not in selected:
        source=root/'app/Voice'/available[0]
        canonical=source/(available[0]+'.aivdic')
        packages=sorted(source.glob('*.aivdic'))
        package=canonical if canonical.is_file() else packages[0]
        data['default_voice']=available[0]+'/'+package.stem
        atomic_json(config_path,data)
    manifest['selected_voices']=available
    manifest['status']='voice-files-updated-needs-check'
    files=manifest['files']
    for key in list(files):
        if key.startswith(('app/Voice/','app/Lang/')):del files[key]
    for folder in [root/'app/Voice',root/'app/Lang']:
        for path in sorted(folder.rglob('*')):
            if path.is_file():files[path.relative_to(root).as_posix()]=sha(path)
    files['config/runtime.json']=sha(config_path)
    registry_path=load_config(config_path).voice_registry
    if registry_path.is_file():files[registry_path.relative_to(root).as_posix()]=sha(registry_path)
    if (root/'voice-imports.json').is_file():files['voice-imports.json']=sha(root/'voice-imports.json')
    atomic_json(root/'install-manifest.json',manifest)


def add_voices(root,voicebanks,languages,selected,report=lambda message:None,dialects=None):
    root,config,manifest=managed_config(root)
    selected=sorted(set(selected));voicebanks=Path(voicebanks);languages=Path(languages)
    with maintenance(root,config):
        for name in selected:
            if os.path.lexists(config.app_dir/'Voice'/name):
                raise ValueError(f'Giọng đã tồn tại: {name}. Không chép đè âm thầm.')
        voice_files,lang_files,registry,catalog=prepare_voice_import(
            voicebanks,languages,selected,load_voice_registry(config.voice_registry),dialects,
            installed_languages=config.app_dir/'Lang')
        verified_files(voicebanks,voice_files,report)
        missing_lang=[]
        for item in lang_files:
            target=config.app_dir/'Lang'/item['path']
            if target.is_file():
                if sha(target)!=item['sha256']:raise ValueError('Lang hiện có khác baseline; không ghi đè')
            else:missing_lang.append(item)
        if missing_lang:verified_files(languages,missing_lang,report)
        stage=Path(tempfile.mkdtemp(prefix='.voice-stage-',dir=root));committed=[];added_lang=[]
        before=(root/'install-manifest.json').read_bytes();before_config=config.config_file.read_bytes()
        before_registry=config.voice_registry.read_bytes()
        catalog_path=root/'voice-imports.json'
        before_catalog=catalog_path.read_bytes() if catalog_path.is_file() else None
        try:
            for item in voice_files:
                target=stage/'Voice'/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(safe_file(voicebanks,item['path']),target)
            for item in missing_lang:
                target=config.app_dir/'Lang'/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
                temporary=stage/('lang-'+str(len(added_lang)))
                shutil.copy2(safe_file(languages,item['path']),temporary)
                # Existing file from another task is never overwritten.
                os.link(temporary,target);added_lang.append(target)
            for name in selected:
                target=config.app_dir/'Voice'/name
                commit_directory(stage/'Voice'/name,target);committed.append(target)
            atomic_json(config.voice_registry,{'schema_version':1,'voices':registry})
            imports=json.loads(before_catalog) if before_catalog else {'schema_version':1,'voices':{}}
            imports['voices'].update(catalog);atomic_json(catalog_path,imports)
            refresh_manifest(root,manifest,set(manifest['selected_voices'])|set(selected))
        except BaseException:
            for path in committed:shutil.rmtree(path)
            for path in added_lang:path.unlink()
            (root/'install-manifest.json').write_bytes(before);config.config_file.write_bytes(before_config)
            config.voice_registry.write_bytes(before_registry)
            if before_catalog is not None:catalog_path.write_bytes(before_catalog)
            elif catalog_path.exists():catalog_path.unlink()
            raise
        finally:shutil.rmtree(stage)
    report('Đã thêm giọng. Mở lại Editor và Refresh danh sách trong Anki; chạy kiểm tra câu mẫu.')


def remove_voice(root,name,report=lambda message:None):
    root,config,manifest=managed_config(root)
    selected=set(manifest['selected_voices'])
    if name not in selected:raise ValueError('Giọng không có trong bản cài đang quản lý')
    if len(selected)<=1:raise ValueError('Giữ ít nhất một giọng để Editor/backend có thể dùng ngay')
    target=config.app_dir/'Voice'/name
    if target.is_symlink() or not target.is_dir():raise ValueError('Thư mục giọng thiếu hoặc là symlink')
    with maintenance(root,config):
        token=time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]
        backup=root/'backups/voices'/token;backup.mkdir(parents=True)
        for path in target.rglob('*'):
            if path.is_symlink():raise ValueError('Không di chuyển voicebank có symlink ngoài manifest')
        checks={p.relative_to(target).as_posix():sha(p) for p in target.rglob('*') if p.is_file()}
        receipt={'schema_version':1,'voice':name,'files':checks,'state':'removing',
                 'language':load_voice_registry(config.voice_registry)[name]['language']}
        atomic_json(backup/'receipt.json',receipt)
        before=(root/'install-manifest.json').read_bytes();before_config=config.config_file.read_bytes()
        commit_directory(target,backup/name)
        try:
            refresh_manifest(root,manifest,selected-{name})
            receipt['state']='removed';atomic_json(backup/'receipt.json',receipt)
        except BaseException:
            commit_directory(backup/name,target)
            (root/'install-manifest.json').write_bytes(before);config.config_file.write_bytes(before_config)
            raise
    report(f'Đã chuyển {name} sang bản dự phòng. Audio đã lưu trong Anki được giữ nguyên.')
    return token


def restore_voice(root,token,report=lambda message:None):
    root,config,manifest=managed_config(root)
    if not token or Path(token).name!=token or token in ('.','..'):raise ValueError('Invalid backup ID')
    backup=root/'backups/voices'/token
    receipt=json.loads((backup/'receipt.json').read_text());name=receipt['voice']
    if not isinstance(name,str) or name in ('','.','..') or Path(name).name!=name or '\\' in name:
        raise ValueError('Invalid backup voice folder')
    registry=load_voice_registry(config.voice_registry)
    language=receipt.get('language') or registry.get(name,{}).get('language')
    if language not in ('standard','kansai'):raise ValueError('Backup voice dialect is unknown')
    with maintenance(root,config):
        for relative,digest in receipt['files'].items():
            if sha(safe_file(backup/name,relative))!=digest:raise ValueError('Backup voice was modified')
        target=config.app_dir/'Voice'/name
        before=(root/'install-manifest.json').read_bytes();before_config=config.config_file.read_bytes()
        before_registry=config.voice_registry.read_bytes()
        commit_directory(backup/name,target)
        try:
            registry[name]={**registry.get(name,{}),'language':language}
            atomic_json(config.voice_registry,{'schema_version':1,'voices':registry})
            refresh_manifest(root,manifest,set(manifest['selected_voices'])|{name})
            receipt['state']='restored';atomic_json(backup/'receipt.json',receipt)
        except BaseException:
            commit_directory(target,backup/name)
            (root/'install-manifest.json').write_bytes(before);config.config_file.write_bytes(before_config)
            config.voice_registry.write_bytes(before_registry)
            raise
    report('Đã khôi phục giọng; mở lại Editor/Refresh Anki và kiểm tra câu mẫu.')
