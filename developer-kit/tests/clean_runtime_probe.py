#!/usr/bin/env python3
"""Offline clean-prefix test; no original prefix, registry or activation imports.

Stages the native engine/dependencies and aitalk.lic from an extracted original
MSI. Language/voice files come from --assets-dir when supplied, otherwise from
the installed copy. The original installed-files and company-files trials are
recorded separately.
All client execution occurs in bubblewrap with a fresh filesystem/network/PID
namespace. This is a local investigation, not a redistributable package.
"""
from array import array
import hashlib
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inside():
    sys.path.insert(0, '/input/tools')
    from run_auth_probe import credentials
    assert not Path('/work/prefix').exists()
    assert not Path('/home/admin/.wine-aivoice').exists()
    assert not Path('/home/admin/.local/share/Anki2').exists()
    report = {'fresh_prefix': True, 'network_namespace': True,
              'personal_home_visible': False, 'controls': [], 'voices': []}
    boot = subprocess.run(['wineboot', '--init'], capture_output=True, timeout=120)
    Path('/work/wineboot.log').write_bytes(boot.stdout + boot.stderr)
    report['wineboot_exit'] = boot.returncode
    assert boot.returncode == 0
    for p in Path('/work/prefix').glob('*.reg'):
        report.setdefault('initial_registry', {})[p.name] = digest(p)
    product, code = credentials(Path('/input/runtime/aitalk.lic'))
    env = os.environ.copy()
    env.update(AITALK_PRODUCT_NAME=product, AITALK_LICENSE_CODE=code)
    base = ['wine', r'Z:\input\tools\auth_probe.exe',
            r'Z:\input\runtime\aitalk_engine.dll']
    voice = 'KotonohaAkane_ns_48'
    args = [r'Z:\input\runtime\aitalk.lic',
            r'Z:\input\Lang\standard\standard.aildic',
            fr'Z:\input\Voice\{voice}\{voice}.aivdic',
            fr'Z:\input\Voice\{voice}\voice.lic']
    for label, fields, expected in [
            ('missing-engine-license', [r'Z:\work\absent.lic'], False),
            ('missing-voice-license', args[:-1] + [r'Z:\work\absent.lic'], False),
            ('original-msi-auth', args[:1], True)]:
        p = subprocess.run(base + fields, env=env, capture_output=True, timeout=120)
        Path('/work/' + label + '.log').write_bytes(p.stdout + p.stderr)
        report['controls'].append({'name': label, 'exit': p.returncode,
                                   'stdout': p.stdout.decode(errors='replace')})
        assert (p.returncode == 0) == expected, label
        print(label, 'exit=' + str(p.returncode), flush=True)
    cases = []
    for folder in sorted(Path('/input/Voice').iterdir()):
        name = folder.name
        dialect = 'kansai' if name == 'KotonohaAkane_ns_48' or name.startswith('akane_west_') else 'standard'
        for i, text in enumerate(['です。', 'こんにちは。今日はいい天気ですね。']):
            output = f'/work/{name}-{i}.wav'
            fields = [text, name, f'Z:\\input\\Voice\\{name}\\{name}.aivdic',
                      f'Z:\\input\\Voice\\{name}\\voice.lic',
                      'Z:' + output.replace('/', '\\'), dialect,
                      f'Z:\\input\\Lang\\{dialect}\\{dialect}.aildic']
            encoded = [s.encode() for s in fields]
            cases.append((name, dialect, text, output,
                          struct.pack('<7I', *(len(s) for s in encoded)) + b''.join(encoded)))
    command = ['wine', r'Z:\input\tools\engine_worker.exe',
               r'Z:\input\runtime\aitalk_engine.dll', r'Z:\input\runtime\aitalk.lic',
               r'Z:\input\Lang\standard\standard.aildic']
    with Path('/work/worker.log').open('wb') as log:
        p = subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
        try:
            stdout, _ = p.communicate(b''.join(c[-1] for c in cases), timeout=240)
        except BaseException:
            p.kill()
            p.communicate()
            raise
    report['worker_exit'] = p.returncode
    assert p.returncode == 0
    assert len(stdout) == 8 * (1 + len(cases)), len(stdout)
    replies = [struct.unpack_from('<iI', stdout, i) for i in range(0, len(stdout), 8)]
    assert replies[0] == (0, 0)
    for (name, dialect, text, output, _), (status, count) in zip(cases, replies[1:]):
        assert status == 0, (name, status)
        with wave.open(output) as w:
            assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 48000)
            pcm = w.readframes(w.getnframes())
        assert len(pcm) == count and any(array('h', pcm))
        report['voices'].append({'voice': name, 'dialect': dialect, 'text': text,
                                 'pcm_bytes': count, 'pcm_sha256': hashlib.sha256(pcm).hexdigest()})
        print(name, dialect, 'pcm_bytes=' + str(count), flush=True)
    report['passed'] = True
    Path('/work/result.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))


def main(assets_dir=None, report_name=None):
    extracted = ROOT / 'cache/clean-msi-extract/ProgramFiles64Folder/AI/AIVoice2/AIVoice2Editor'
    installed = ROOT / 'AIVoice2Editor'
    languages = assets_dir / 'Lang' if assets_dir else installed / 'Lang'
    voicebanks = assets_dir / 'voicebanks' if assets_dir else installed / 'Voice'
    assert extracted.is_dir(), 'Extract the original MSI with msiextract first'
    run = Path(tempfile.mkdtemp(prefix='clean-runtime-', dir=ROOT / 'cache'))
    stage = run / 'input'
    (stage / 'runtime').mkdir(parents=True)
    (stage / 'tools').mkdir()
    work = run / 'work'
    work.mkdir()
    etc = run / 'etc'
    etc.mkdir()
    uid = os.getuid()
    (etc / 'passwd').write_text(f'admin:x:{uid}:{os.getgid()}:Clean test:/home/admin:/bin/sh\n')
    (etc / 'group').write_text(f'admin:x:{os.getgid()}:\n')
    (etc / 'nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
    (etc / 'hosts').write_text('127.0.0.1 localhost aivoice-clean\n')
    (etc / 'machine-id').write_text(os.urandom(16).hex() + '\n')
    manifest = []

    def copy(source, relative, provenance):
        dest = stage / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        manifest.append({'path': str(relative), 'source': str(source), 'origin': provenance,
                         'bytes': dest.stat().st_size, 'sha256': digest(dest)})

    # Import closure only, excluding the Editor and activation/license-manager DLLs.
    available = {p.name.lower(): p for p in extracted.glob('*.dll')}
    available['aitalk_engine.dll'] = extracted / 'Lib/AITalk/aitalk_engine.dll'
    pending = ['aitalk_engine.dll']
    done = set()
    while pending:
        key = pending.pop()
        if key in done:
            continue
        done.add(key)
        source = available[key]
        copy(source, Path('runtime') / source.name, 'original-editor-msi')
        info = subprocess.run(['x86_64-w64-mingw32-objdump', '-p', str(source)],
                              capture_output=True, text=True, check=True).stdout
        pending.extend(n.lower() for n in re.findall(r'DLL Name:\s*(\S+)', info)
                       if n.lower() in available and n.lower() not in done)
    copy(extracted / 'Lib/AITalk/aitalk.lic', Path('runtime/aitalk.lic'), 'original-editor-msi')
    for p in sorted(languages.glob('*/*.aildic')):
        copy(p, Path('Lang') / p.relative_to(languages),
             'company-supplied-language-package' if assets_dir else 'installed-copy-language-package')
    bank_count = 0
    for p in sorted(voicebanks.glob('*/*.aivdic')):
        if p.stem != p.parent.name:
            continue
        bank_count += 1
        copy(p, Path('Voice') / p.relative_to(voicebanks),
             'company-supplied-voice-package' if assets_dir else 'installed-copy-voice-package')
        lic = p.parent / 'voice.lic'
        copy(lic, Path('Voice') / lic.relative_to(voicebanks),
             'company-supplied-voice-license' if assets_dir else 'installed-copy-voice-license-unverified-installer-origin')
    assert bank_count, 'No canonical voicebanks found'
    for stem in ['engine_worker', 'auth_probe']:
        subprocess.run(['x86_64-w64-mingw32-gcc', '-Wall', '-Wextra', '-Werror', '-O2',
                        str(ROOT / 'src/daemon' / (stem + '.c')), '-o', str(stage / 'tools' / (stem + '.exe'))], check=True)
    shutil.copyfile(ROOT / 'src/daemon/run_auth_probe.py', stage / 'tools/run_auth_probe.py')
    shutil.copyfile(Path(__file__), stage / 'tools/clean_runtime_probe.py')
    (run / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    command = ['bwrap', '--unshare-all', '--die-with-parent', '--new-session',
               '--hostname', 'aivoice-clean', '--ro-bind', '/usr', '/usr',
               '--symlink', 'usr/bin', '/bin', '--symlink', 'usr/lib', '/lib',
               '--symlink', 'usr/lib', '/lib64', '--ro-bind', str(etc), '/etc',
               '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
               '--dir', '/home/admin', '--ro-bind', str(stage), '/input',
               '--bind', str(work), '/work', '--chdir', '/work', '--clearenv',
               '--setenv', 'PATH', '/usr/bin', '--setenv', 'LANG', 'C.UTF-8',
               '--setenv', 'WINEPREFIX', '/work/prefix', '--setenv', 'WINEDEBUG', '-all',
               '--setenv', 'WINEDLLOVERRIDES', 'mscoree,mshtml=',
               '/usr/bin/python3', '/input/tools/clean_runtime_probe.py', '--inside']
    (run / 'isolation-command.json').write_text(json.dumps(command, indent=2))
    print('Local test directory:', run, flush=True)
    with (run / 'run.log').open('wb') as log:
        p = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=480)
    print((run / 'run.log').read_text(errors='replace'), end='')
    report_dir = ROOT / 'notes/evidence/clean-runtime'
    if report_name:
        report_dir /= report_name
    report_dir.mkdir(parents=True, exist_ok=True)
    for filename in ['manifest.json', 'isolation-command.json', 'run.log']:
        shutil.copyfile(run / filename, report_dir / filename)
    result = work / 'result.json'
    if result.exists():
        shutil.copyfile(result, report_dir / 'result.json')
    for log in work.glob('*.log'):
        shutil.copyfile(log, report_dir / log.name)
    assert p.returncode == 0, (p.returncode, str(run))
    print(f'PASS: offline clean prefix; original MSI engine; all {bank_count} voices synthesized')


if __name__ == '__main__':
    if '--inside' in sys.argv:
        inside()
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--assets-dir', type=Path,
                            help='Company-supplied directory with Lang/ and voicebanks/')
        parser.add_argument('--report-name', choices=['installed-assets', 'company-assets'])
        args = parser.parse_args()
        main(args.assets_dir, args.report_name)
