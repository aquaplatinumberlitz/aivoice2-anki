#!/usr/bin/env python3
"""Modern desktop manager and CLI for A.I.VOICE2 + Anki."""
import argparse
import json
from pathlib import Path
import sys
import shutil
import subprocess

from install_core import ROOT,RUNTIME, dependency_report, initialize_runtime, install_files
from voice_sources import scan_voicebanks,parse_dialects
from runtime_config import load_voice_registry


def wizard(payload, baseline, managed_root=None):
    try:
        from desktop_ui import run_app
    except ImportError as error:
        message=('Giao diện cần Qt 6 cho Python (PySide6 hoặc PyQt6). '
                 'Cài gói PySide6/PyQt6 cho Python hệ thống theo hướng dẫn START_HERE_VI.md. '
                 'Backend TTS và addon Anki không bị thay đổi bởi thông báo này.')
        if shutil.which('kdialog'):subprocess.run(['kdialog','--title','A.I.VOICE2 + Anki','--error',message])
        elif shutil.which('zenity'):subprocess.run(['zenity','--error','--title=A.I.VOICE2 + Anki','--text='+message])
        raise RuntimeError(message+' Chi tiết: '+str(error)) from error
    return run_app(payload,baseline,managed_root)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload',type=Path,default=ROOT/'build/payload')
    parser.add_argument('--baseline',type=Path,default=ROOT/'release/release-inputs.json')
    parser.add_argument('--managed-root',type=Path)
    sub=parser.add_subparsers(dest='command')
    sub.add_parser('dependencies')
    install=sub.add_parser('install')
    for field in ['msi','languages','voicebanks','destination']:install.add_argument('--'+field,type=Path,required=True)
    install.add_argument('--voices',nargs='+',required=True)
    install.add_argument('--files-only',action='store_true',help='Stage/commit files only; initialize Wine separately')
    install.add_argument('--dialect',action='append',default=[],metavar='FOLDER=standard|kansai')
    init=sub.add_parser('initialize');init.add_argument('--config',type=Path,required=True)
    add=sub.add_parser('voices-add')
    for field in ['root','voicebanks','languages']:add.add_argument('--'+field,type=Path,required=True)
    add.add_argument('--voices',nargs='+',required=True)
    add.add_argument('--dialect',action='append',default=[],metavar='FOLDER=standard|kansai')
    scan=sub.add_parser('voices-scan');scan.add_argument('--voicebanks',type=Path,required=True)
    remove=sub.add_parser('voices-remove');remove.add_argument('--root',type=Path,required=True)
    remove.add_argument('--voice',required=True)
    restore=sub.add_parser('voices-restore');restore.add_argument('--root',type=Path,required=True)
    restore.add_argument('--backup',required=True)
    activate=sub.add_parser('activate');activate.add_argument('--root',type=Path,required=True)
    activate.add_argument('--addons-dir',type=Path)
    activate.add_argument('--no-service',action='store_true');activate.add_argument('--no-desktop',action='store_true')
    stop=sub.add_parser('stop-service');stop.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='dependencies':print(json.dumps(dependency_report(),indent=2));return
    if args.command=='voices-scan':
        registry_path=args.payload/'runtime/voice_registry.json'
        if not registry_path.is_file():registry_path=RUNTIME/'voice_registry.json'
        print(json.dumps(scan_voicebanks(args.voicebanks,load_voice_registry(registry_path)),ensure_ascii=False,indent=2));return
    if args.command=='initialize':print(initialize_runtime(args.config,report=print));return
    if args.command=='activate':
        from integrations import activate
        print(json.dumps(activate(args.root,args.addons_dir,not args.no_service,not args.no_desktop,print),ensure_ascii=False,indent=2));return
    if args.command=='stop-service':
        from integrations import stop_owned_service
        stop_owned_service(args.root);return
    if args.command in ('voices-add','voices-remove','voices-restore'):
        from voice_manager import add_voices,remove_voice,restore_voice
        if args.command=='voices-add':add_voices(args.root,args.voicebanks,args.languages,args.voices,report=print,dialects=parse_dialects(args.dialect))
        elif args.command=='voices-remove':print('BACKUP',remove_voice(args.root,args.voice,report=print))
        else:restore_voice(args.root,args.backup,report=print)
        return
    if args.command=='install':
        config=install_files(args.msi,args.languages,args.voicebanks,args.voices,args.destination,args.payload,
                             baseline=args.baseline,report=print,dialects=parse_dialects(args.dialect))
        print('CONFIG',config)
        if not args.files_only:print('SAMPLE',initialize_runtime(config,report=print))
        return
    wizard(args.payload,args.baseline,args.managed_root)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(f'Thiết lập chưa hoàn tất: {error}',file=sys.stderr);sys.exit(1)
