#!/usr/bin/env python3
"""Exercise shared GUI/backend config in an offline fresh, relocated Wine runtime.

Mounts only explicit app/runtime inputs. No personal home, original prefix,
compiler sources, Anki collection or running production service is used.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[1]


def inside():
    expected_voices=int(sys.argv[sys.argv.index('--expected-voices')+1]) if '--expected-voices' in sys.argv else 4
    base = Path('/work/Người mới có dấu và khoảng trắng')
    runtime = base / 'runtime'
    sys.path.insert(0, str(runtime))
    from runtime_config import load_config
    config_path = base / 'config/runtime.json'
    config_path.parent.mkdir(parents=True)
    shutil.copy2(runtime / 'voice_registry.json', config_path.parent / 'voices.json')
    config_path.write_text(json.dumps(dict(schema_version=1, app_dir='../app',
        runtime_dir='../runtime', engine_prefix='../prefixes/engine', gui_prefix='../prefixes/gui',
        voice_registry='voices.json', cache_dir='../cache', log_dir='../logs',
        port=17863), ensure_ascii=False))
    config = load_config(config_path)
    assert not Path('/home/admin/.wine-aivoice').exists()
    os.environ.update(HOME='/work/home', DISPLAY=':97', WINEDEBUG='-all',
        WINEDLLOVERRIDES='mscoree,mshtml=', LIBGL_ALWAYS_SOFTWARE='1',
        __EGL_VENDOR_LIBRARY_FILENAMES='/usr/share/glvnd/egl_vendor.d/50_mesa.json',
        XDG_RUNTIME_DIR='/work/xdg', FONTCONFIG_FILE='/etc/fontconfig-clean.conf')
    for p in ['/work/home','/work/xdg','/tmp/.X11-unix','/work/fontcache']:
        Path(p).mkdir(parents=True, exist_ok=True)
    os.chmod('/work/xdg',0o700)
    xvfb = subprocess.Popen(['Xvfb', ':97', '-screen','0','1920x1080x24','-nolisten','tcp','-ac'],
                            stdout=open('/work/xvfb.log','wb'), stderr=subprocess.STDOUT)
    time.sleep(1)
    assert xvfb.poll() is None, 'Xvfb failed; inspect xvfb.log'
    server = gui = None
    result = {'fresh_prefixes':True, 'offline_namespace':True, 'relocated_unicode_paths':True,
              'shared_app_dir':str(config.app_dir), 'requests':[]}
    try:
        for label,prefix in [('engine',config.engine_prefix),('gui',config.gui_prefix)]:
            assert not prefix.exists()
            prefix.parent.mkdir(parents=True,exist_ok=True)
            with open('/work/wineboot-'+label+'.log','wb') as log:
                subprocess.run(['wineboot','--init'],env=dict(os.environ,WINEPREFIX=str(prefix)),
                               stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
        server = subprocess.Popen([sys.executable,str(runtime/'server.py'),'--config',str(config_path)],
            stdout=open('/work/server.log','wb'),stderr=subprocess.STDOUT,cwd='/tmp')
        deadline=time.monotonic()+100
        while True:
            if server.poll() is not None: raise RuntimeError('Server failed; inspect server.log')
            try:
                with urllib.request.urlopen(config.api_url+'/healthz',timeout=1) as response:
                    assert json.load(response)['ready'];break
            except (OSError,urllib.error.URLError):
                if time.monotonic()>deadline: raise
                time.sleep(.5)
        # GUI and engine share the app while using separately initialized prefixes.
        gui = subprocess.Popen([sys.executable,str(runtime/'runtime_cli.py'),'--config',str(config_path),'gui'],
            stdout=open('/work/gui-launch.log','wb'),stderr=subprocess.STDOUT,cwd='/tmp')
        with urllib.request.urlopen(config.api_url+'/v1/voices') as response:
            items=json.load(response)['voices']
        assert len(items)==expected_voices,items
        hashes={}
        for item in items:
            body=json.dumps(dict(text='です。',voice=item['id'])).encode()
            request=urllib.request.Request(config.api_url+'/v1/speak',body,{'Content-Type':'application/json'})
            with urllib.request.urlopen(request,timeout=120) as response:
                audio=response.read();cache=response.headers['X-Aivoice2-Cache']
            with wave.open(io.BytesIO(audio)) as wav:
                assert (wav.getnchannels(),wav.getsampwidth(),wav.getframerate())==(1,2,48000)
                pcm=wav.readframes(wav.getnframes());assert any(pcm)
            digest=hashlib.sha256(pcm).hexdigest();hashes[item['folder']]=digest
            result['requests'].append(dict(voice=item['id'],language=item['language'],
                                           frames=len(pcm)//2,pcm_sha256=digest,cache=cache))
        if 'KotonohaAkane_ns_48' in hashes and 'KotonohaAoi_ns_48' in hashes:
            assert hashes['KotonohaAkane_ns_48']!=hashes['KotonohaAoi_ns_48']
        # Confirm a warmed worker/cache does not mix text or voices.
        with urllib.request.urlopen(request,timeout=120) as response:
            assert response.headers['X-Aivoice2-Cache']=='hit'
            assert response.read()==audio
        time.sleep(4)
        assert gui.poll() is None,'GUI exited'
        subprocess.run(['xdotool','mousemove','621','212','click','1'],check=True)
        time.sleep(.5)
        subprocess.run(['xdotool','mousemove','705','294','click','1'],check=True)
        time.sleep(1)
        subprocess.run(['import','-window','root','/work/shared-gui-license.png'],check=True)
        assert gui.poll() is None
        if '--with-anki' in sys.argv:
            os.environ.update(QTWEBENGINE_DISABLE_SANDBOX='1',QTWEBENGINE_CHROMIUM_FLAGS='--no-sandbox --disable-gpu',
                              QT_QPA_PLATFORM='xcb')
            for legacy in [False, True]:
                label='legacy' if legacy else 'new'
                command=[sys.executable,str(runtime/'anki_gui_smoke.py'),'--api-url',config.api_url,
                         '--expected-voices',str(expected_voices),'--evidence-dir','/work/anki-'+label,
                         '--addon-source',str(runtime/'anki-addon'),'--temp-dir','/work','--null-audio']
                if legacy:command.append('--legacy')
                with open('/work/anki-'+label+'.log','wb') as log:
                    subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=150,check=True)
            result['anki_new_and_legacy_pipeline']=True
            result['anki_playback_scope']='Player start hook, valid preview WAV, same media bytes; no physical audio device in namespace'
        if '--voice-lifecycle' in sys.argv:
            # All file mutations are in the disposable Voice bind mount, with
            # GUI and backend stopped before moving any real dictionary files.
            # No customer-facing manager is claimed by this diagnostic.
            from runtime_cli import diagnose
            lifecycle=[]
            def api(path,body=None):
                payload=None if body is None else json.dumps(body).encode()
                req=urllib.request.Request(config.api_url+path,payload,{'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=120) as response:
                    return response.read()
            def listing():return json.loads(api('/v1/voices'))
            def pcm_for(voice=None,text='です。'):
                body={'text':text}
                if voice:body['voice']=voice
                with wave.open(io.BytesIO(api('/v1/speak',body))) as w:
                    return hashlib.sha256(w.readframes(w.getnframes())).hexdigest()
            def stop_backend():
                nonlocal server
                if server:
                    server.terminate();server.wait(timeout=10);server=None
                subprocess.run(['wineserver','-k'],env=dict(os.environ,WINEPREFIX=str(config.engine_prefix)),
                               capture_output=True,timeout=15,check=True)
            def start_backend():
                nonlocal server
                log=open('/work/lifecycle-server.log','ab')
                server=subprocess.Popen([sys.executable,str(runtime/'server.py'),'--config',str(config_path)],
                                        stdout=log,stderr=subprocess.STDOUT,cwd='/tmp')
                log.close()
                deadline=time.monotonic()+80
                while True:
                    if server.poll() is not None:raise RuntimeError('Lifecycle backend failed')
                    try:
                        assert json.loads(api('/healthz'))['ready'];break
                    except OSError:
                        if time.monotonic()>deadline:raise
                        time.sleep(.4)
            def denied(voice):
                try:api('/v1/speak',{'text':'です。','voice':voice})
                except urllib.error.HTTPError as error:assert error.code==400
                else:raise AssertionError('Removed/unregistered voice must not synthesize from stale state')
            def save_registry(data):
                temporary=config.voice_registry.with_suffix('.tmp')
                temporary.write_text(json.dumps(data));temporary.replace(config.voice_registry)
            subprocess.run(['wineserver','-k'],env=dict(os.environ,WINEPREFIX=str(config.gui_prefix)),
                           capture_output=True,timeout=15,check=True)
            gui.wait(timeout=15);gui=None
            folder=config.app_dir/'Voice'
            backup=base/'voice-backups';backup.mkdir()
            mikoto='MeikaMikoto_ns_48';mikoto_id=mikoto+'/'+mikoto
            akane='KotonohaAkane_ns_48';akane_id=akane+'/'+akane
            # Repeated switches run in the same worker, bypassing cache via a
            # second sentence to ensure actual dictionary/dialect transitions.
            for text in ['です。です。','です。です。です。']:
                switched={}
                for voice in ['KotonohaAoi_ns_48','KotonohaAkane_ns_48','MeikaHime_ns_48','MeikaMikoto_ns_48']:
                    switched[voice]=pcm_for(voice+'/'+voice,text)
                assert switched['KotonohaAoi_ns_48']!=switched['KotonohaAkane_ns_48']
            lifecycle.append({'case':'switch-four-voices-twice-with-fresh-text','passed':True})
            stop_backend();shutil.move(str(folder/mikoto),str(backup/mikoto));start_backend()
            assert len(listing()['voices'])==3;denied(mikoto_id)
            lifecycle.append({'case':'remove-selected-mikoto','voices':3,'removed_request_status':400,'passed':True})
            stop_backend()
            registry=json.loads(config.voice_registry.read_text())
            entry=registry['voices'].pop(mikoto);save_registry(registry)
            shutil.move(str(backup/mikoto),str(folder/mikoto));start_backend()
            assert len(listing()['voices'])==3;denied(mikoto_id)
            assert diagnose(config)['unregistered_voices']==[mikoto]
            lifecycle.append({'case':'add-bank-without-dialect-registration','listed':False,'passed':True})
            registry['voices'][mikoto]=entry;save_registry(registry)
            assert len(listing()['voices'])==4
            assert pcm_for(mikoto_id)==hashes[mikoto]
            lifecycle.append({'case':'register-dialect-and-synthesize','voices':4,'pcm_sha256':hashes[mikoto],'passed':True})
            assert pcm_for(akane_id)==hashes[akane]
            stop_backend();shutil.move(str(folder/akane),str(backup/akane));start_backend()
            current=listing();assert len(current['voices'])==3
            assert current['default_voice'].startswith('KotonohaAoi_ns_48/')
            assert pcm_for()==hashes['KotonohaAoi_ns_48'];denied(akane_id)
            lifecycle.append({'case':'remove-default-akane','fallback':current['default_voice'],'passed':True})
            # Inspect the existing GUI profile after a voice was removed. Its
            # stock preset behavior is evidence, not assumed auto-cleanup.
            gui=subprocess.Popen([sys.executable,str(runtime/'runtime_cli.py'),'--config',str(config_path),'gui'],
                stdout=open('/work/gui-after-remove-launch.log','wb'),stderr=subprocess.STDOUT,cwd='/tmp')
            time.sleep(20)
            assert gui.poll() is None,'GUI exited after default voice removal'
            subprocess.run(['import','-window','root','/work/gui-after-remove.png'],check=True)
            subprocess.run(['xdotool','mousemove','621','212','click','1'],check=True);time.sleep(.4)
            subprocess.run(['xdotool','mousemove','705','294','click','1'],check=True);time.sleep(1)
            subprocess.run(['import','-window','root','/work/gui-license-after-remove.png'],check=True)
            subprocess.run(['wineserver','-k'],env=dict(os.environ,WINEPREFIX=str(config.gui_prefix)),capture_output=True,timeout=15)
            gui.wait(timeout=15);gui=None
            stop_backend();shutil.move(str(backup/akane),str(folder/akane));start_backend()
            assert len(listing()['voices'])==4
            assert pcm_for(akane_id)==hashes[akane]
            lifecycle.append({'case':'restore-akane','voices':4,'passed':True})
            stop_backend()
            license_path=folder/mikoto/'voice.lic';shutil.move(str(license_path),str(backup/'mikoto-voice.lic'))
            start_backend();assert len(listing()['voices'])==3;denied(mikoto_id)
            assert mikoto in diagnose(config)['incomplete_voices']
            lifecycle.append({'case':'missing-voice-license','listed':False,'passed':True})
            stop_backend();shutil.move(str(backup/'mikoto-voice.lic'),str(license_path));start_backend()
            assert len(listing()['voices'])==4
            assert pcm_for(mikoto_id)==hashes[mikoto]
            lifecycle.append({'case':'restore-license','voices':4,'passed':True})
            result['voice_lifecycle']=lifecycle
            result['voice_management_scope']='Backend/config/file lifecycle on disposable copies; customer manager not implemented; GUI removal screenshots need visual review'
        result.update(passed=True,cache_hit_checked=True,gui_and_engine_concurrent=True)
        Path('/work/result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False),flush=True)
    finally:
        if server:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait()
        # Namespace-owned prefixes only; never target the desktop/user prefix.
        for prefix in [config.engine_prefix,config.gui_prefix]:
            subprocess.run(['wineserver','-k'],env=dict(os.environ,WINEPREFIX=str(prefix)),
                           capture_output=True,timeout=15)
        if gui:
            try:gui.wait(timeout=10)
            except subprocess.TimeoutExpired:gui.kill();gui.wait()
        xvfb.terminate();xvfb.wait(timeout=5)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--with-anki',action='store_true')
    parser.add_argument('--voice-lifecycle',action='store_true')
    parser.add_argument('--expected-voices',type=int,default=4)
    args=parser.parse_args()
    (ROOT/'cache').mkdir(exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='portable-runtime-',dir=ROOT/'cache'))
    runtime=run/'runtime';runtime.mkdir()
    for name in ['runtime_config.py','runtime_cli.py','server.py','run_auth_probe.py','voice_registry.json']:
        candidate=args.runtime/name
        shutil.copy2(candidate if candidate.is_file() else ROOT/'src/daemon'/name,runtime/name)
    shutil.copy2(args.runtime/'engine_worker.exe',runtime/'engine_worker.exe')
    shutil.copy2(Path(__file__),runtime/'probe.py')
    if args.with_anki:
        shutil.copy2(ROOT/'tests/anki_gui_smoke.py',runtime/'anki_gui_smoke.py')
        package=args.runtime.parent/'anki/aivoice2-local.ankiaddon'
        if package.is_file():
            import zipfile
            with zipfile.ZipFile(package) as archive:archive.extractall(runtime/'anki-addon')
        else:
            shutil.copytree(ROOT/'src/anki-addon',runtime/'anki-addon',ignore=shutil.ignore_patterns('__pycache__'))
    work=run/'work';work.mkdir()
    if args.voice_lifecycle:
        # Reflink when supported; never hardlink mutable test voice data.
        subprocess.run(['cp','-a','--reflink=auto',str(args.app.resolve()/'Voice'),str(work/'voice-files')],check=True)
    etc=run/'etc';etc.mkdir()
    (etc/'passwd').write_text(f'newbie:x:{os.getuid()}:{os.getgid()}:Test:/work/home:/bin/sh\n')
    (etc/'group').write_text(f'newbie:x:{os.getgid()}:\n')
    (etc/'nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
    (etc/'hosts').write_text('127.0.0.1 localhost\n')
    (etc/'machine-id').write_text(os.urandom(16).hex()+'\n')
    shutil.copytree('/etc/fonts',etc/'fonts',symlinks=True)
    (etc/'fontconfig-clean.conf').write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>/usr/share/fonts</dir><cachedir>/work/fontcache</cachedir></fontconfig>')
    target='/work/Người mới có dấu và khoảng trắng'
    command=['bwrap','--unshare-all','--die-with-parent','--new-session',
        '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib',
        '--symlink','usr/lib','/lib64','--ro-bind',str(etc),'/etc','--proc','/proc','--dev','/dev',
        '--tmpfs','/tmp','--bind',str(work),'/work','--dir',target,
        '--ro-bind',str(args.app.resolve()),target+'/app','--ro-bind',str(runtime),target+'/runtime',
        '--clearenv','--setenv','PATH','/usr/bin','--setenv','LANG','C.UTF-8',
        '/usr/bin/python3',target+'/runtime/probe.py','--inside']
    if args.with_anki:command.append('--with-anki')
    command+=['--expected-voices',str(args.expected_voices)]
    if args.voice_lifecycle:
        # Place the writable disposable voice overlay before clearenv/exec.
        index=command.index('--clearenv')
        command[index:index]=['--bind',str(work/'voice-files'),target+'/app/Voice']
        command.append('--voice-lifecycle')
    (run/'isolation-command.json').write_text(json.dumps(command,ensure_ascii=False,indent=2)+'\n')
    print('RUN_DIR',run,flush=True)
    sys.exit(subprocess.call(command))


if __name__=='__main__':
    inside() if '--inside' in sys.argv else main()
