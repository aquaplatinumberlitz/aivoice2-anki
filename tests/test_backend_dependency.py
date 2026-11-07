"""Pinned backend distribution and manager compatibility regression checks."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/setup'))
import install_core
import server


class BackendDependencyTests(unittest.TestCase):
    def test_payload_is_the_pinned_streaming_backend(self):
        manifest = install_core.verify_payload(ROOT / 'build/payload')
        self.assertEqual(manifest['backend'], json.loads((ROOT / 'aivoice2api.lock.json').read_text()))
        worker = json.loads((ROOT / 'build/payload/runtime/worker-manifest.json').read_text())
        self.assertEqual(worker['worker_protocol'], 'vntext-pcm-metrics-v1')
        self.assertFalse((ROOT / 'src/daemon').exists())
        self.assertFalse((ROOT / 'archive/src/daemon').exists())

    def test_rehashed_foreign_backend_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = Path(directory) / 'payload'
            shutil.copytree(ROOT / 'build/payload', payload)
            (payload / 'runtime/server.py').write_text('# substituted backend\n')
            path = payload / 'payload-manifest.json'
            manifest = json.loads(path.read_text())
            manifest['files']['runtime/server.py'] = install_core.sha(payload / 'runtime/server.py')
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'pinned backend artifact'):
                install_core.verify_payload(payload)

    def test_initializer_and_installed_manager_share_the_new_runtime(self):
        with tempfile.TemporaryDirectory(prefix='aivoice-manager-') as directory:
            root = Path(directory)
            for name in ['config', 'app', 'prefixes/gui/dosdevices', 'prefixes/engine/dosdevices']:
                (root / name).mkdir(parents=True)
            shutil.copytree(ROOT / 'build/payload/runtime', root / 'runtime')
            shutil.copytree(ROOT / 'src/setup', root / 'manager/src/setup',
                            ignore=shutil.ignore_patterns('__pycache__'))
            for prefix in ['gui', 'engine']:
                (root / 'prefixes' / prefix / 'system.reg').write_text('fixture')
            config = dict(schema_version=1, app_dir='../app', runtime_dir='../runtime',
                          engine_prefix='../prefixes/engine', gui_prefix='../prefixes/gui',
                          cache_dir='../cache', log_dir='../logs',
                          voice_registry='../runtime/voice_registry.json', default_voice='aoi/aoi')
            (root / 'config/runtime.json').write_text(json.dumps(config))
            (root / 'install-manifest.json').write_text(json.dumps(
                {'schema_version': 1, 'selected_voices': ['aoi']}))
            wav = root / 'cache/sample.wav'
            engine = MagicMock()
            engine.speak.return_value = wav, False, {'queue_ms': 0}
            with patch.object(server, 'Engine', return_value=engine), patch.object(
                    server, 'voices', return_value={'aoi/aoi': {'folder': 'aoi'}}):
                self.assertEqual(install_core.initialize_runtime(root / 'config/runtime.json'), wav)
            engine.stop.assert_called_once()
            manifest = json.loads((root / 'install-manifest.json').read_text())
            self.assertEqual(manifest['status'], 'native-checked')
            code = ('import sys; from pathlib import Path; '
                    'sys.path.insert(0,sys.argv[1]); import install_core,server; '
                    'assert Path(server.__file__).parent==Path(sys.argv[2]); '
                    'assert install_core.RUNTIME==Path(sys.argv[2])')
            subprocess.run([sys.executable, '-c', code, str(root / 'manager/src/setup'),
                            str(root / 'runtime')], check=True,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))


if __name__ == '__main__':
    unittest.main()
