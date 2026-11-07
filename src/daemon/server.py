#!/usr/bin/env python3
"""Local A.I.VOICE2 HTTP service, one persistent Wine engine, serial synthesis."""
from __future__ import annotations

import hashlib
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import select
import struct
import subprocess
import threading
import time
import uuid
import wave

from run_auth_probe import ENGINE_SHA256, credentials
from runtime_config import load_config, load_voice_registry, install_drive_aliases, acquire_runtime_lease

DEFAULT_VOICE = 'KotonohaAkane_ns_48/KotonohaAkane_ns_48'
CONFIG = None


def voices(config=None):
    config = config or CONFIG or load_config()
    registry = load_voice_registry(config.voice_registry)
    result = {}
    for package in sorted((config.app_dir / 'Voice').glob('*/*.aivdic')):
        canonical = package.parent / (package.parent.name + '.aivdic')
        if canonical.is_file() and package != canonical:
            continue
        license_path = package.parent / 'voice.lic'
        if license_path.is_file():
            identity = package.relative_to(config.app_dir / 'Voice').with_suffix('').as_posix()
            # Unknown dialects must be registered and checked before synthesis.
            entry = registry.get(package.parent.name)
            if entry is None:
                continue
            language = entry['language']
            language_package = config.app_dir / 'Lang' / language / (language + '.aildic')
            if not language_package.is_file():
                continue
            result[identity] = {'id': identity, 'name': package.stem,
                                'folder': package.parent.name,
                                'package': package, 'license': license_path,
                                'language': language,
                                'language_package': language_package}
    return result


class Engine:
    def __init__(self, config=None):
        self.config = config
        self.lock = threading.Lock()
        self.process = None
        self.ready = False
        self.log = None
        self.version = ''
        self.lease = None

    def read_reply(self, timeout=120):
        deadline = time.monotonic() + timeout
        data = bytearray()
        while len(data) < 8:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise TimeoutError('Engine timed out; retry to restart it')
            part = os.read(self.process.stdout.fileno(), 8 - len(data))
            if not part:
                raise RuntimeError('Engine stopped; check journalctl --user -u aivoice2-tts')
            data.extend(part)
        return struct.unpack('<iI', data)

    def stop(self):
        self.ready = False
        if self.process:
            try:
                self.process.stdin.close()
                self.process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                self.process.kill()
                self.process.wait(timeout=5)
            self.process.stdout.close()
            self.process = None
        if self.log:
            self.log.close()
            self.log = None
        if self.lease:
            self.lease.close()
            self.lease = None

    def start(self):
        self.stop()
        config = self.config or CONFIG or load_config()
        self.config = config
        engine_path = config.app_dir / 'aitalk_engine.dll'
        if hashlib.sha256(engine_path.read_bytes()).hexdigest() != ENGINE_SHA256:
            raise ValueError('Engine differs from the inspected artifact')
        exe = config.worker
        if not exe.is_file():
            raise ValueError('Thiếu engine_worker.exe đã build. Chạy sửa cài đặt; runtime không tự biên dịch.')
        self.version = hashlib.sha256(exe.read_bytes()).hexdigest()
        license_path = config.app_dir / 'Lib' / 'AITalk' / 'aitalk.lic'
        product, code = credentials(license_path)
        env = os.environ.copy()
        env.update(WINEPREFIX=str(config.engine_prefix), WINEDEBUG='-all',
                   AITALK_PRODUCT_NAME=product, AITALK_LICENSE_CODE=code)
        config.cache_dir.mkdir(parents=True, exist_ok=True)
        config.log_dir.mkdir(parents=True, exist_ok=True)
        self.lease = acquire_runtime_lease(config)
        install_drive_aliases(config, config.engine_prefix)
        self.log = (config.log_dir / 'engine-worker.log').open('ab', buffering=0)
        command = ['wine', config.wine_path(exe), config.wine_path(engine_path),
                   config.wine_path(license_path),
                   config.wine_path(config.app_dir / 'Lang/standard/standard.aildic')]
        self.process = subprocess.Popen(command, env=env, cwd=config.cache_dir,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.log, bufsize=0)
        try:
            status, _ = self.read_reply()
            if status:
                raise RuntimeError(f'Engine initialization failed ({status})')
            self.ready = True
        except Exception:
            self.stop()
            raise

    def speak(self, text, voice_id):
        if not isinstance(text, str) or not text.strip() or '\x00' in text:
            raise ValueError('Text is required')
        text = text.strip()
        if len(text) > 4096 or len(text.encode('utf-8')) > 16384:
            raise ValueError('Text is too long (maximum 4096 characters)')
        available = voices(self.config)
        if not isinstance(voice_id, str) or voice_id not in available:
            raise ValueError('Unknown voice; refresh the voice list')
        voice = available[voice_id]
        with self.lock:
            if not self.ready or self.process.poll() is not None:
                self.start()
            signature = [text, voice_id, ENGINE_SHA256, self.version,
                         voice['package'].stat().st_mtime_ns,
                         voice['license'].stat().st_mtime_ns,
                         voice['language'], voice['language_package'].stat().st_mtime_ns]
            digest = hashlib.sha256(json.dumps(signature, ensure_ascii=False).encode()).hexdigest()
            output = self.config.cache_dir / f'aivoice2_{digest}.wav'
            if output.is_file():
                return output, True
            temporary = self.config.cache_dir / f'{uuid.uuid4().hex}.wav'
            fields = [text, voice['name'], self.config.wine_path(voice['package']),
                      self.config.wine_path(voice['license']), self.config.wine_path(temporary),
                      voice['language'], self.config.wine_path(voice['language_package'])]
            encoded = [f.encode('utf-8') for f in fields]
            try:
                packet = struct.pack('<7I', *(len(f) for f in encoded)) + b''.join(encoded)
                # FileIO writes can be partial for packets above PIPE_BUF.
                view = memoryview(packet)
                while view:
                    count = self.process.stdin.write(view)
                    if not count:
                        raise BrokenPipeError('Engine input closed')
                    view = view[count:]
                self.process.stdin.flush()
                status, count = self.read_reply()
                if status:
                    raise RuntimeError(f'Synthesis failed ({status}) for {voice["name"]}')
                with wave.open(str(temporary), 'rb') as wav:
                    if (wav.getnchannels() != 1 or wav.getsampwidth() != 2
                            or not wav.getnframes() or wav.getnframes() * 2 != count):
                        raise RuntimeError('Engine returned invalid audio')
                temporary.replace(output)
                return output, False
            except (OSError, TimeoutError):
                self.stop()
                raise
            finally:
                temporary.unlink(missing_ok=True)


engine = Engine()


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, content_type='application/json', **headers):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        for key, value in headers.items():
            self.send_header(key.replace('_', '-'), value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path == '/healthz':
            ready = bool(engine.ready and engine.process and engine.process.poll() is None)
            self.send(200 if ready else 503, {'ready': ready, 'engine': 'A.I.VOICE2',
                                            'instance_id': CONFIG.instance_id})
        elif self.path == '/v1/voices':
            items = [{k: v for k, v in item.items()
                      if k not in ('package', 'license', 'language_package')}
                     for item in voices().values()]
            preferred = CONFIG.default_voice
            default = preferred if any(v['id'] == preferred for v in items) else (
                items[0]['id'] if items else None)
            self.send(200, {'voices': items, 'default_voice': default})
        else:
            self.send(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path != '/v1/speak':
            self.send(404, {'error': 'Not found'})
            return
        self.connection.settimeout(15)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('Invalid request size')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError('Expected a JSON object')
            available = voices(CONFIG)
            default = CONFIG.default_voice if CONFIG.default_voice in available else next(iter(available), None)
            path, cached = engine.speak(body.get('text'), body.get('voice', default))
            self.send(200, path.read_bytes(), 'audio/wav',
                      X_Aivoice2_Filename=path.name, X_Aivoice2_Cache='hit' if cached else 'miss')
        except (ValueError, UnicodeError) as error:
            self.send(400, {'error': str(error)})
        except Exception as error:
            print(f'Synthesis error: {error}', flush=True)
            self.send(503, {'error': str(error)})


def main():
    global CONFIG, engine
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config')
    args = parser.parse_args()
    CONFIG = load_config(args.config)
    engine = Engine(CONFIG)
    if CONFIG.development_fallback:
        print('Development fallback: configure AIVOICE2_CONFIG for a managed installation.', flush=True)
    try:
        server = ThreadingHTTPServer(('127.0.0.1', CONFIG.port), Handler)
    except OSError as error:
        raise SystemExit(f'Không mở được {CONFIG.api_url}; kiểm tra dịch vụ/cổng đang dùng: {error}')
    server.daemon_threads = True
    try:
        engine.start()
        print(f'A.I.VOICE2 ready at {CONFIG.api_url}', flush=True)
        server.serve_forever()
    finally:
        server.server_close()
        engine.stop()


if __name__ == '__main__':
    main()
