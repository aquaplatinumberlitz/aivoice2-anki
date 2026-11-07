#!/usr/bin/env python3
"""First install and voice maintenance from separate inputs in a fresh offline namespace."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def inside():
    os.environ.update(HOME='/work/home',XDG_CACHE_HOME='/work/cache',XDG_STATE_HOME='/work/state',
        XDG_RUNTIME_DIR='/work/xdg',DISPLAY=':97',WINEDEBUG='-all',WINEDLLOVERRIDES='mscoree,mshtml=',
        LIBGL_ALWAYS_SOFTWARE='1',__EGL_VENDOR_LIBRARY_FILENAMES='/usr/share/glvnd/egl_vendor.d/50_mesa.json',
        QT_QPA_PLATFORM='xcb',QTWEBENGINE_DISABLE_SANDBOX='1',QTWEBENGINE_CHROMIUM_FLAGS='--no-sandbox --disable-gpu',
        FONTCONFIG_FILE='/etc/fontconfig-clean.conf')
    for name in ['/work/home','/work/cache','/work/state','/work/xdg','/work/fontcache','/tmp/.X11-unix']:
        Path(name).mkdir(parents=True,exist_ok=True)
    os.chmod('/work/xdg',0o700)
    assert not Path('/home/admin').exists()
    xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','1920x1080x24','-nolisten','tcp','-ac'],
        stdout=open('/work/xvfb.log','wb'),stderr=subprocess.STDOUT)
    time.sleep(1);assert xvfb.poll() is None
    target=Path('/work/Khách mới có dấu/bản cài')
    config_file=target/'config/runtime.json'
    command=[sys.executable,'/project/src/setup/manager.py','--payload','/input/payload']
    result={'fresh_offline_install':True,'selected_initial_voice':'KotonohaAoi_ns_48','steps':[]}
    gui=server=None
    def run(label,arguments):
        with open('/work/'+label+'.log','wb') as log:
            subprocess.run(command+arguments,stdout=log,stderr=subprocess.STDOUT,timeout=240,check=True)
        result['steps'].append({'case':label,'passed':True})
    try:
        if '--extended-voices' in sys.argv:
            run('install-bank-outside-original-baseline',['install','--msi','/input/AIVoice2Editor.msi',
                '--languages','/input/Lang','--voicebanks','/input/voicebanks','--destination',str(target),
                '--voices','KizunaAkari_ns_48','akane_west_emo_48'])
            names=sorted(p.name for p in (target/'app/Voice').iterdir())
            assert names==['KizunaAkari_ns_48','akane_west_emo_48'],names
            result.pop('selected_initial_voice',None)
            result['selected_initial_voices']=names
            manifest=json.loads((target/'install-manifest.json').read_text())
            assert manifest['status']=='native-checked'
            assert len(manifest['voice_checks'])==2
            run('remove-new-bank',['voices-remove','--root',str(target),'--voice','KizunaAkari_ns_48'])
            token=next((target/'backups/voices').iterdir()).name
            run('restore-new-bank',['voices-restore','--root',str(target),'--backup',token])
            run('synthesize-both-restored-banks',['initialize','--config',str(config_file)])
            sys.path.insert(0,str(target/'runtime'))
            from server import voices
            from runtime_config import load_config
            assert len(voices(load_config(config_file)))==2
            result.update(passed=True,physical_audio_checked=False,
                scope='Actual install/init/remove/restore outside four-voice baseline; Akane/Kizuna dialects selected automatically by publisher policy')
            Path('/work/result.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(result),flush=True)
            return
        if '--with-wizard' in sys.argv:
            sys.path.insert(0,'/project/src/setup')
            from desktop_ui import ManagerWindow,AddVoicesDialog,STYLE
            from qt_compat import QtWidgets as W,QtCore
            from runtime_config import load_voice_registry
            app=W.QApplication.instance() or W.QApplication([])
            app.setStyle('Fusion');app.setStyleSheet(STYLE)
            window=ManagerWindow(Path('/input/payload'),Path('/project/release/release-inputs.json'))
            errors=[];complete=[];play_requests=[]
            def fail(message):
                errors.append(message)
                if window.demo_dialog:window.demo_dialog.stop()
                window.busy=False
                window.close();app.quit()
            W.QMessageBox.warning=lambda parent,title,text:fail(title+': '+text)
            def begin():
                try:
                    for key,value in dict(msi='/input/AIVoice2Editor.msi',languages='/input/Lang',
                                           voicebanks='/input/voicebanks',destination=str(target)).items():
                        window.fields[key].setText(value)
                    window.scan_install();window.install_voices.select_only(['KotonohaAoi_ns_48'])
                    window.service_option.setChecked(False);window.anki_option.setChecked(True)
                    window.start_install()
                except Exception as error:fail(str(error))
            def after_install(success):
                try:
                    assert success,'Install task failed'
                    assert window.progress.value()==100 and window.percent.text()=='100%'
                    assert window.open_editor_button.isEnabled() and window.open_anki_button.isEnabled()
                    window.grab().save('/work/setup-wizard-complete.png')
                    # Add flow uses its own source picker, independent of install fields.
                    dialog=AddVoicesDialog(window,load_voice_registry(target/'runtime/voice_registry.json'),['KotonohaAoi_ns_48'])
                    dialog.source.setText('/input/voicebanks');dialog.scan()
                    assert dialog.voices.table.rowCount()==4
                    assert 'KotonohaAoi_ns_48' not in dialog.voices.selected()
                    dialog.close()
                    window.open_preview();demo=window.demo_dialog
                    demo.playback.requested.connect(lambda path:play_requests.append(path))
                    demo.speak();QtCore.QTimer.singleShot(100,check_preview)
                except Exception as error:fail(str(error))
            def check_preview():
                try:
                    demo=window.demo_dialog
                    if demo.busy:QtCore.QTimer.singleShot(100,check_preview);return
                    assert demo.wav and demo.wav.is_file(),'No WAV from preview'
                    assert play_requests,'Preview did not request audio playback'
                    demo.grab().save('/work/preview-dialog.png');demo.stop();demo.close()
                    complete.append(True);window.close();app.quit()
                except Exception as error:fail(str(error))
            window.task_finished.connect(after_install);window.show()
            QtCore.QTimer.singleShot(200,begin)
            QtCore.QTimer.singleShot(240000,lambda:fail('Qt wizard timed out'))
            app.exec()
            assert not errors,errors
            assert complete,'Wizard did not complete'
            result['steps'].append({'case':'qt-wizard-install-and-progress-100','passed':True})
            result['steps'].append({'case':'independent-add-voices-dialog','passed':True})
            result['steps'].append({'case':'audible-preview-wav-and-player-request','passed':True,'physical_device_asserted':False})
        else:
            run('install-aoi',['install','--msi','/input/AIVoice2Editor.msi','--languages','/input/Lang',
                '--voicebanks','/input/voicebanks','--destination',str(target),'--voices','KotonohaAoi_ns_48'])
        assert [p.name for p in (target/'app/Voice').iterdir()]==['KotonohaAoi_ns_48']
        assert not (target/'app/Lang/kansai').exists()
        assert json.loads((target/'install-manifest.json').read_text())['status']=='native-checked'
        run('add-akane',['voices-add','--root',str(target),'--voicebanks','/input/voicebanks',
            '--languages','/input/Lang','--voices','KotonohaAkane_ns_48'])
        assert (target/'app/Lang/kansai/kansai.aildic').is_file()
        sys.path.insert(0,str(target/'runtime'))
        from runtime_config import load_config
        from server import Engine
        config=load_config(config_file)
        def synth():
            engine=Engine(config)
            try:
                path,_=engine.speak('です。','KotonohaAkane_ns_48/KotonohaAkane_ns_48')
                import wave
                with wave.open(str(path)) as wav:
                    pcm=wav.readframes(wav.getnframes())
                    assert wav.getnframes()==61920
                return hashlib.sha256(pcm).hexdigest()
            finally:engine.stop()
        assert synth()=='69f5f03c844431d3bc4260a1f84ea82da2495d5d19add51794287a0b310a8032'
        data=json.loads(config_file.read_text());data['default_voice']='KotonohaAkane_ns_48/KotonohaAkane_ns_48'
        config_file.write_text(json.dumps(data))
        run('remove-default-akane',['voices-remove','--root',str(target),'--voice','KotonohaAkane_ns_48'])
        assert json.loads(config_file.read_text())['default_voice'].startswith('KotonohaAoi_ns_48/')
        assert not (target/'app/Voice/KotonohaAkane_ns_48').exists()
        token=next((target/'backups/voices').iterdir()).name
        run('restore-akane',['voices-restore','--root',str(target),'--backup',token])
        assert synth()=='69f5f03c844431d3bc4260a1f84ea82da2495d5d19add51794287a0b310a8032'
        server=subprocess.Popen([sys.executable,str(target/'runtime/server.py'),'--config',str(config_file)],
            stdout=open('/work/server.log','wb'),stderr=subprocess.STDOUT)
        deadline=time.monotonic()+90
        while True:
            if server.poll() is not None:raise RuntimeError('Installed server exited')
            try:
                with urllib.request.urlopen(config.api_url+'/healthz',timeout=1) as response:
                    assert json.load(response)['ready'];break
            except OSError:
                if time.monotonic()>deadline:raise
                time.sleep(.4)
        # Actual worker owns a shared lease: maintenance must refuse the change.
        with open('/work/refuse-active-runtime.log','wb') as log:
            blocked=subprocess.run(command+['voices-remove','--root',str(target),'--voice','KotonohaAkane_ns_48'],
                stdout=log,stderr=subprocess.STDOUT,timeout=20)
        assert blocked.returncode!=0
        assert (target/'app/Voice/KotonohaAkane_ns_48').is_dir()
        result['steps'].append({'case':'refuse-maintenance-while-engine-running','passed':True})
        addons=Path('/work/customer-anki/addons21');(addons/'aivoice2_local').mkdir(parents=True)
        (addons/'aivoice2_local/meta.json').write_text(json.dumps({'config':{'audio_field':'Audio','source_field':'Japanese'}}))
        (addons/'unrelated').mkdir();(addons/'unrelated/keep.txt').write_text('keep')
        run('integrate-anki-files',['activate','--root',str(target),'--addons-dir',str(addons),'--no-service','--no-desktop'])
        settings=json.loads((addons/'aivoice2_local/meta.json').read_text())['config']
        assert settings['audio_field']=='Audio' and settings['source_field']=='Japanese'
        assert settings['api_url']==config.api_url
        assert (addons/'unrelated/keep.txt').read_text()=='keep'
        gui=subprocess.Popen([sys.executable,str(target/'runtime/runtime_cli.py'),'--config',str(config_file),'gui'],
            stdout=open('/work/gui-launch.log','wb'),stderr=subprocess.STDOUT)
        # Use the .ankiaddon produced by the payload builder, not a user addon.
        addon=addons/'aivoice2_local'
        for legacy in [False,True]:
            label='anki-legacy' if legacy else 'anki-new'
            args=[sys.executable,'/project/tests/anki_gui_smoke.py','--api-url',config.api_url,
                  '--expected-voices','2','--evidence-dir','/work/'+label,'--addon-source',str(addon),'--temp-dir','/work','--null-audio']
            if legacy:args.append('--legacy')
            with open('/work/'+label+'.log','wb') as log:
                subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=150,check=True)
            result['steps'].append({'case':label,'passed':True})
        runtime_cli=target/'runtime/runtime_cli.py'
        with open('/work/verify-files.json','wb') as log:
            subprocess.run([sys.executable,str(runtime_cli),'--config',str(config_file),'verify-files'],
                           stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
        subprocess.run([sys.executable,str(runtime_cli),'--config',str(config_file),'--output','/work/support.zip','export-support'],
                       stdout=subprocess.DEVNULL,check=True)
        import zipfile
        with zipfile.ZipFile('/work/support.zip') as bundle:
            assert bundle.namelist()==['support-summary.json']
            summary=bundle.read('support-summary.json').decode()
            assert str(target) not in summary and 'こんにちは' not in summary
            assert '[APP]' in summary
        result['steps'].append({'case':'installed-manifest-and-support-export','passed':True})
        assert gui.poll() is None
        subprocess.run(['import','-window','root','/work/installed-gui.png'],check=True)
        result.update(passed=True,physical_audio_checked=False,
            anki_audio_sink='null sink in temporary Anki base only; actual WAV/player hooks still checked',
            scope='Installer core/wizard when enabled, real voice lifecycle and installed Anki addon; real user service tested separately')
        Path('/work/result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)
    finally:
        if server:server.terminate();server.wait(timeout=10)
        if config_file.is_file():
            sys.path.insert(0,str(target/'runtime'))
            from runtime_config import load_config
            config=load_config(config_file)
            for prefix in [config.engine_prefix,config.gui_prefix]:
                subprocess.run(['wineserver','-k'],env=dict(os.environ,WINEPREFIX=str(prefix)),capture_output=True,timeout=15)
        if gui:
            try:gui.wait(timeout=10)
            except subprocess.TimeoutExpired:gui.kill();gui.wait()
        xvfb.terminate();xvfb.wait(timeout=5)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload',type=Path,required=True)
    parser.add_argument('--msi',type=Path,required=True)
    parser.add_argument('--assets-dir',type=Path,required=True)
    parser.add_argument('--with-wizard',action='store_true')
    parser.add_argument('--extended-voices',action='store_true')
    args=parser.parse_args()
    (ROOT/'cache').mkdir(exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='setup-clean-',dir=ROOT/'cache'))
    work=run/'work';work.mkdir()
    project=run/'project';project.mkdir()
    shutil.copytree(ROOT/'src/setup',project/'src/setup',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT/'src/daemon',project/'src/daemon',ignore=shutil.ignore_patterns('__pycache__','build','*.exe'))
    (project/'release').mkdir();shutil.copy2(ROOT/'release/release-inputs.json',project/'release/release-inputs.json')
    (project/'tests').mkdir()
    shutil.copy2(ROOT/'tests/anki_gui_smoke.py',project/'tests/anki_gui_smoke.py')
    shutil.copy2(Path(__file__),project/'tests/setup_clean_probe.py')
    etc=run/'etc';etc.mkdir()
    (etc/'passwd').write_text(f'customer:x:{os.getuid()}:{os.getgid()}:Customer:/work/home:/bin/sh\n')
    (etc/'group').write_text(f'customer:x:{os.getgid()}:\n')
    (etc/'nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
    (etc/'hosts').write_text('127.0.0.1 localhost\n')
    (etc/'machine-id').write_text(os.urandom(16).hex()+'\n')
    shutil.copytree('/etc/fonts',etc/'fonts',symlinks=True)
    (etc/'fontconfig-clean.conf').write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>/usr/share/fonts</dir><cachedir>/work/fontcache</cachedir></fontconfig>')
    command=['bwrap','--unshare-all','--die-with-parent','--new-session',
        '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib','/lib64',
        '--ro-bind',str(etc),'/etc','--proc','/proc','--dev','/dev','--tmpfs','/tmp',
        '--bind',str(work),'/work','--ro-bind',str(project),'/project',
        '--ro-bind',str(args.payload.resolve()),'/input/payload',
        '--ro-bind',str(args.msi.resolve()),'/input/AIVoice2Editor.msi',
        '--ro-bind',str((args.assets_dir/'Lang').resolve()),'/input/Lang',
        '--ro-bind',str((args.assets_dir/('voicebanks' if (args.assets_dir/'voicebanks').is_dir() else 'Voice')).resolve()),'/input/voicebanks',
        '--clearenv','--setenv','PATH','/usr/bin','--setenv','LANG','C.UTF-8',
        '/usr/bin/python3','/project/tests/setup_clean_probe.py','--inside']
    if args.with_wizard:command.append('--with-wizard')
    if args.extended_voices:command.append('--extended-voices')
    (run/'isolation-command.json').write_text(json.dumps(command,indent=2)+'\n')
    print('RUN_DIR',run,flush=True);sys.exit(subprocess.call(command))


if __name__=='__main__':inside() if '--inside' in sys.argv else main()
