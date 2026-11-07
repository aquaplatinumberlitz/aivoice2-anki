#!/usr/bin/env python3
"""Stock MSI GUI and headless license matrix in a fresh offline container.

Interactive stdin accepts JSON argv arrays for diagnostic commands inside the
container; 'quit' terminates only this test's processes and namespace.
Run in a PTY (tty=true in exec_command); otherwise stdin EOF closes the test.
--gui-only skips the headless matrix; --omit-licenses removes .lic files only
from the disposable app tree and implies --gui-only.
--gui-snapshot tests a candidate data/app.so without changing an installation.
"""
import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def inside():
    sys.path.insert(0, '/input/tools')
    from run_auth_probe import credentials
    assert not Path('/home/admin/.wine-aivoice').exists()
    Path('/work/home').mkdir()
    Path('/work/fontcache').mkdir()
    Path('/work/xdg').mkdir(mode=0o700)
    Path('/tmp/.X11-unix').mkdir(mode=0o1777, exist_ok=True)
    os.environ.update(HOME='/work/home', XDG_CACHE_HOME='/work/home/.cache', DISPLAY=':97',
                      XDG_RUNTIME_DIR='/work/xdg', LIBGL_ALWAYS_SOFTWARE='1',
                      __EGL_VENDOR_LIBRARY_FILENAMES='/usr/share/glvnd/egl_vendor.d/50_mesa.json')
    if '--trace-adapter' in sys.argv:
        os.environ['AIVOICE2_ADAPTER_TRACE'] = r'Z:\work\adapter-calls.jsonl'
    xvfb_log = Path('/work/xvfb.log').open('wb')
    xvfb = subprocess.Popen(['Xvfb', ':97', '-screen', '0', '1920x1080x24', '-nolisten', 'tcp', '-ac'],
                            stdout=xvfb_log, stderr=subprocess.STDOUT)
    time.sleep(1)
    assert xvfb.poll() is None, 'Xvfb failed; see xvfb.log'
    with Path('/work/wineboot.log').open('wb') as f:
        subprocess.run(['wineboot', '--init'], stdout=f, stderr=subprocess.STDOUT, timeout=120, check=True)
    product, code = (credentials(Path('/input/app/Lib/AITalk/aitalk.lic'))
                     if '--gui-only' not in sys.argv else ('', ''))
    env = dict(os.environ, AITALK_PRODUCT_NAME=product, AITALK_LICENSE_CODE=code)
    matrix = []
    for label, mode, engine_license, voice_license in ([] if '--gui-only' in sys.argv else [
        ('skip-auth', 'skip-auth', r'Z:\work\absent.lic', 'NULL'),
        ('null-auth', 'null-auth', r'Z:\work\absent.lic', 'NULL'),
        ('missing-engine-license', 'normal', r'Z:\work\absent.lic', 'NULL'),
        ('null-voice-license', 'normal', r'Z:\input\app\Lib\AITalk\aitalk.lic', 'NULL'),
        ('empty-voice-license', 'normal', r'Z:\input\app\Lib\AITalk\aitalk.lic', 'EMPTY'),
        ('missing-voice-license', 'normal', r'Z:\input\app\Lib\AITalk\aitalk.lic', r'Z:\work\absent.lic'),
        ('stock-files', 'normal', r'Z:\input\app\Lib\AITalk\aitalk.lic', r'Z:\input\app\Voice\KotonohaAoi_ns_48\voice.lic'),
    ]):
        command = ['wine', r'Z:\input\tools\headless_license_probe.exe',
                   r'Z:\input\app\aitalk_engine.dll', mode, engine_license,
                   r'Z:\input\app\Lang\standard\standard.aildic', voice_license,
                   r'Z:\input\app\Voice\KotonohaAoi_ns_48\KotonohaAoi_ns_48.aivdic',
                   'Z:\\work\\' + label + '.wav']
        p = subprocess.run(command, env=env, capture_output=True, timeout=120)
        Path('/work/' + label + '.log').write_bytes(p.stdout + p.stderr)
        rec = dict(case=label, exit=p.returncode, stdout=p.stdout.decode(errors='replace'))
        matrix.append(rec)
        print(json.dumps(rec), flush=True)
    Path('/work/headless-matrix.json').write_text(json.dumps(matrix, indent=2))
    gui_log = Path('/work/gui.log').open('wb')
    gui = subprocess.Popen(['wine', r'Z:\input\app\aivoice.exe'], cwd='/input/app',
                           stdout=gui_log, stderr=subprocess.STDOUT)
    print('GUI_STARTED', gui.pid, flush=True)
    try:
        for line in sys.stdin:
            if line.strip() == 'quit':
                break
            try:
                args = json.loads(line)
                p = subprocess.run(args, capture_output=True, timeout=30)
                print(json.dumps(dict(exit=p.returncode, stdout=p.stdout.decode(errors='replace')[:10000],
                                      stderr=p.stderr.decode(errors='replace')[:2000])), flush=True)
            except Exception as e:
                print(str(e), flush=True)
    finally:
        subprocess.run(['wineserver', '-k'], capture_output=True, timeout=15)
        gui.wait(timeout=15)
        xvfb.terminate()
        xvfb.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gui-only', action='store_true')
    parser.add_argument('--omit-licenses', action='store_true')
    parser.add_argument('--license-dll', type=Path,
                        help='Explicit license-manager candidate; copied only into the disposable app')
    parser.add_argument('--license-adapter', type=Path,
                        help='Explicit ailm.dll candidate; copied only into the disposable app')
    parser.add_argument('--trace-adapter', action='store_true',
                        help='Record helper validation arguments in the disposable work directory')
    parser.add_argument('--gui-snapshot', type=Path,
                        help='Explicit candidate data/app.so; copied only into the disposable app')
    args = parser.parse_args()
    r = Path(tempfile.mkdtemp(prefix='gui-license-', dir=ROOT/'cache'))
    app = r/'input/app'
    msi = ROOT/'cache/clean-msi-extract/ProgramFiles64Folder/AI/AIVoice2/AIVoice2Editor'
    shutil.copytree(msi, app)
    if args.gui_snapshot:
        shutil.copyfile(args.gui_snapshot, app/'data/app.so')
    if args.license_dll:
        shutil.copyfile(args.license_dll, app/'AI.Framework.License.dll')
    if args.license_adapter:
        shutil.copyfile(args.license_adapter, app/'ailm.dll')
    assets = Path('/home/admin/Downloads/A.I.VOICE2 2.14.1')
    shutil.copytree(assets/'Lang', app/'Lang')
    shutil.copytree(assets/'voicebanks', app/'Voice')
    if '--omit-licenses' in sys.argv:
        for path in app.rglob('*.lic'):
            path.unlink()
    # The MSI layout expects install-time DLL search paths; the inspected Editor
    # installation also puts this identical engine beside its native dependencies.
    shutil.copyfile(app/'Lib/AITalk/aitalk_engine.dll', app/'aitalk_engine.dll')
    tools = r/'input/tools'
    tools.mkdir()
    shutil.copyfile(ROOT/'src/daemon/run_auth_probe.py', tools/'run_auth_probe.py')
    shutil.copyfile(Path(__file__), tools/'gui_license_probe.py')
    subprocess.run(['x86_64-w64-mingw32-gcc', '-Wall', '-Wextra', '-Werror', '-O2',
                    '-I', str(ROOT/'src/daemon'), str(ROOT/'tests/headless_license_probe.c'),
                    '-o', str(tools/'headless_license_probe.exe')], check=True)
    work = r/'work'
    work.mkdir()
    etc = r/'etc'
    shutil.copytree(ROOT/'cache/clean-runtime-c_vlf5gg/etc', etc)
    (etc/'machine-id').write_text(os.urandom(16).hex()+'\n')
    shutil.copytree('/etc/fonts', etc/'fonts', symlinks=True)
    (etc/'fontconfig-clean.conf').write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>/usr/share/fonts</dir><cachedir>/work/fontcache</cachedir></fontconfig>')
    manifest = []
    for p in sorted(app.rglob('*')):
        if p.is_file():
            with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
            manifest.append(dict(path=str(p.relative_to(app)), sha256=sha, bytes=p.stat().st_size))
    (r/'manifest.json').write_text(json.dumps(manifest,indent=2))
    cmd=['bwrap','--unshare-all','--die-with-parent','--new-session','--hostname','gui-license-clean',
         '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib',
         '--symlink','usr/lib','/lib64','--ro-bind',str(etc),'/etc','--proc','/proc','--dev','/dev',
         '--tmpfs','/tmp','--dir','/home/admin','--ro-bind',str(r/'input'),'/input',
         '--bind',str(work),'/work','--chdir','/work','--clearenv','--setenv','PATH','/usr/bin',
         '--setenv','LANG','C.UTF-8','--setenv','WINEPREFIX','/work/prefix','--setenv','WINEDEBUG','-all',
         '--setenv','WINEDLLOVERRIDES','mscoree,mshtml=','--setenv','FONTCONFIG_FILE','/etc/fontconfig-clean.conf',
         '/usr/bin/python3','/input/tools/gui_license_probe.py','--inside']
    if '--gui-only' in sys.argv or '--omit-licenses' in sys.argv:
        cmd.append('--gui-only')
    if args.trace_adapter:
        cmd.append('--trace-adapter')
    (r/'isolation-command.json').write_text(json.dumps(cmd,indent=2))
    print('RUN_DIR',r,flush=True)
    sys.exit(subprocess.call(cmd))


if __name__=='__main__':
    inside() if '--inside' in sys.argv else main()
