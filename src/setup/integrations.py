"""Managed service/desktop/addon integration; no Anki collection is opened."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

from install_core import atomic_json,commit_directory,sha
from runtime_cli import render_service
from voice_manager import managed_config


def instance_id(root):return hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()[:12]


def desktop_quote(value):
    value=str(value)
    if any(c in value for c in '\n\r\x00'):raise ValueError('Invalid desktop path')
    escaped=value.replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')
    return '"'+escaped.replace('\\','\\\\')+'"'


def anki_is_running():
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            args=(proc/'cmdline').read_bytes().split(b'\0')
            names=[Path(arg.decode(errors='replace')).name.lower() for arg in args[:3] if arg]
            if any(name in ('anki','anki.py','anki.exe') for name in names):return True
        except OSError:continue
    return False


def install_addon(root,addons_directory):
    root,config,manifest=managed_config(root)
    if anki_is_running():raise ValueError('Lưu công việc và đóng Anki trước khi cài/cập nhật addon.')
    archive=root/'anki/aivoice2-local.ankiaddon'
    expected=manifest['files'].get('anki/aivoice2-local.ankiaddon')
    if not expected or sha(archive)!=expected:raise ValueError('Addon package differs from the installed manifest')
    addons_directory=Path(addons_directory).expanduser().resolve()
    addons_directory.mkdir(parents=True,exist_ok=True)
    target=addons_directory/'aivoice2_local'
    if target.is_symlink():raise ValueError('Không ghi đè addon target là symlink')
    staging=Path(tempfile.mkdtemp(prefix='.aivoice2-addon-',dir=addons_directory))
    backup=None
    try:
        with zipfile.ZipFile(archive) as package:
            allowed={'__init__.py','card_model.py','editor_compat.py','selection.js','config.json','config.md','manifest.json'}
            if set(package.namelist())!=allowed:raise ValueError('Addon archive has unexpected members')
            for info in package.infolist():
                if ((info.external_attr>>16)&0o170000)==0o120000:raise ValueError('Symlink in addon archive')
                (staging/info.filename).write_bytes(package.read(info))
        # Preserve user settings in meta.json, updating only this installation's
        # API endpoint. Existing unknown addon-owned files are retained in backup.
        meta_path=target/'meta.json'
        meta=json.loads(meta_path.read_text()) if meta_path.is_file() else {}
        settings=meta.get('config') or {}
        settings['api_url']=config.api_url
        meta.update(name='A.I.VOICE2 Local TTS',config=settings)
        atomic_json(staging/'meta.json',meta)
        if target.exists():
            backup=Path(tempfile.mkdtemp(prefix='addon-',dir=ensure_backup_dir(root)))/'aivoice2_local'
            # The Anki profile can be on another filesystem, so copying backup
            # first is required; then the old folder is parked beside target.
            shutil.copytree(target,backup)
            parked=addons_directory/('.aivoice2-old-'+instance_id(root))
            if parked.exists():raise ValueError('Old addon update is pending; inspect the parked backup first')
            commit_directory(target,parked)
        else:parked=None
        try:commit_directory(staging,target)
        except BaseException:
            if parked:commit_directory(parked,target)
            raise
        if parked:shutil.rmtree(parked)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return {'addon_path':str(target),'backup':str(backup) if backup else None,'api_url':config.api_url}


def ensure_backup_dir(root):
    path=Path(root)/'backups/integration';path.mkdir(parents=True,exist_ok=True);return path


def choose_port(start=17862):
    for port in range(start,min(start+100,65536)):
        with socket.socket() as test:
            try:test.bind(('127.0.0.1',port))
            except OSError:continue
            return port
    raise ValueError('Không có cổng loopback trống trong dải đã chọn')


def activate(root,addons_directory=None,enable_service=True,desktop=True,report=lambda message:None):
    root,config,manifest=managed_config(root)
    if addons_directory and anki_is_running():raise ValueError('Đóng Anki trước khi tích hợp.')
    prior_path=root/'integration.json'
    prior=json.loads(prior_path.read_text()) if prior_path.is_file() else {}
    unit_name='aivoice2-local-'+instance_id(root)+'.service'
    config_home=Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')
    data_home=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')
    if enable_service:
        if not shutil.which('systemctl'):raise ValueError('Bản Linux này cần systemd user service hoặc cấu hình thủ công')
        unit_path=config_home/'systemd/user'/unit_name
        expected_unit=prior.get('unit_sha256')
        if unit_path.exists() and (not expected_unit or sha(unit_path)!=expected_unit):
            raise ValueError('Unit đã tồn tại nhưng không thuộc trạng thái quản lý này')
        active=subprocess.run(['systemctl','--user','is-active','--quiet',unit_name]).returncode==0
        if not active:
            port=choose_port(config.port)
            if port!=config.port:
                data=json.loads(config.config_file.read_text());data['port']=port;atomic_json(config.config_file,data)
                from runtime_config import load_config
                config=load_config(config.config_file)
        unit=render_service(config,root/'runtime/server.py')
        unit_path.parent.mkdir(parents=True,exist_ok=True)
        # Record ownership before start so interrupted activation can be resumed.
        unit_path.write_text(unit)
        prior.update(unit_name=unit_name,unit_path=str(unit_path),unit_sha256=sha(unit_path),status='service-start-pending')
        atomic_json(prior_path,prior)
        subprocess.run(['systemctl','--user','daemon-reload'],check=True)
        subprocess.run(['systemctl','--user','enable','--now',unit_name],check=True)
        deadline=time.monotonic()+90
        while True:
            try:
                with urllib.request.urlopen(config.api_url+'/healthz',timeout=2) as response:
                    health=json.load(response)
                    if health.get('ready') and health.get('instance_id')==config.instance_id:break
            except OSError:
                pass
            if time.monotonic()>deadline:
                raise ValueError('Backend chưa sẵn sàng hoặc endpoint thuộc bản cài khác. Kiểm tra service; có thể chạy lại bước tích hợp.')
            time.sleep(.3)
        report('Đã bật backend tự khởi động cho tài khoản hiện tại.')
    if desktop:
        desktop_path=data_home/'applications'/('aivoice2-local-'+instance_id(root)+'.desktop')
        if desktop_path.exists() and prior.get('desktop_sha256')!=sha(desktop_path):
            raise ValueError('Shortcut đã thay đổi bên ngoài; không tự chép đè')
        command=' '.join(desktop_quote(value) for value in [sys.executable,root/'runtime/runtime_cli.py',
                                                           '--config',config.config_file,'gui'])
        desktop_path.parent.mkdir(parents=True,exist_ok=True)
        desktop_path.write_text('[Desktop Entry]\nType=Application\nVersion=1.0\nName=A.I.VOICE2 + Anki\n'
            'Comment=Voice editor and local Anki TTS\nExec='+command+'\nIcon=audio-card\nTerminal=false\nCategories=AudioVideo;Audio;\n')
        prior.update(desktop_path=str(desktop_path),desktop_sha256=sha(desktop_path))
        atomic_json(prior_path,prior)
        manager_path=desktop_path.with_name(desktop_path.stem+'-manager.desktop')
        manager_command=' '.join(desktop_quote(value) for value in [sys.executable,root/'manager/src/setup/manager.py',
                                                                    '--managed-root',root])
        manager_path.write_text('[Desktop Entry]\nType=Application\nVersion=1.0\nName=Quản lý A.I.VOICE2 + Anki\n'
            'Exec='+manager_command+'\nIcon=preferences-desktop\nTerminal=false\nCategories=AudioVideo;Audio;\n')
        prior.update(manager_desktop_path=str(manager_path),manager_desktop_sha256=sha(manager_path))
    if addons_directory:
        prior.update(install_addon(root,addons_directory))
        report('Đã cài addon và kết nối endpoint. Mở lại Anki để dùng.')
    prior.update(status='activated',api_url=config.api_url)
    atomic_json(prior_path,prior)
    manifest['files']['config/runtime.json']=sha(config.config_file)
    atomic_json(root/'install-manifest.json',manifest)
    return prior


def stop_owned_service(root):
    root,config,manifest=managed_config(root)
    data=json.loads((root/'integration.json').read_text())
    expected='aivoice2-local-'+instance_id(root)+'.service'
    if data.get('unit_name')!=expected:raise ValueError('No owned service to stop')
    subprocess.run(['systemctl','--user','stop',expected],check=True)


def start_owned_service(root):
    root,config,manifest=managed_config(root)
    data=json.loads((root/'integration.json').read_text())
    expected='aivoice2-local-'+instance_id(root)+'.service'
    if data.get('unit_name')!=expected:raise ValueError('No owned service to start')
    subprocess.run(['systemctl','--user','start',expected],check=True)
