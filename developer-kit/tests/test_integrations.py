"""Addon migration preserves settings and unrelated addons; integration stays scoped."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/setup'))
from install_core import atomic_json,sha
from integrations import install_addon,activate,instance_id,stop_owned_service


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'managed';self.root.mkdir()
        atomic_json(self.root/'config/runtime.json',dict(schema_version=1,app_dir='../app',runtime_dir='../runtime',
            engine_prefix='../prefixes/engine',gui_prefix='../prefixes/gui',voice_registry='../voices.json'))
        archive=self.root/'anki/aivoice2-local.ankiaddon';archive.parent.mkdir()
        self.archive=archive
        with zipfile.ZipFile(archive,'w') as package:
            for name in ['__init__.py','card_model.py','editor_compat.py','selection.js','config.json','config.md','manifest.json']:
                package.writestr(name,'{}' if name.endswith('.json') else '# fixture')
        atomic_json(self.root/'install-manifest.json',dict(schema_version=1,selected_voices=['Aoi'],
            files={'anki/aivoice2-local.ankiaddon':sha(archive)}))
        self.addons=Path(self.temp.name)/'anki/addons21'
        self.proc=patch('integrations.anki_is_running',return_value=False);self.proc.start();self.addCleanup(self.proc.stop)

    def test_addon_preserves_existing_settings_and_unrelated_files(self):
        target=self.addons/'aivoice2_local'
        atomic_json(target/'meta.json',{'config':{'audio_field':'MyAudio','voice':'Aoi/Aoi'}})
        other=self.addons/'other/keep';other.parent.mkdir();other.write_text('keep')
        result=install_addon(self.root,self.addons)
        meta=json.loads((target/'meta.json').read_text())
        self.assertEqual(meta['config']['audio_field'],'MyAudio')
        self.assertEqual(meta['config']['api_url'],'http://127.0.0.1:17862')
        self.assertEqual(other.read_text(),'keep')
        self.assertTrue((Path(result['backup'])/'meta.json').is_file())

    def test_running_anki_rejected_before_any_target_write(self):
        with patch('integrations.anki_is_running',return_value=True):
            with self.assertRaises(ValueError):install_addon(self.root,self.addons)
        self.assertFalse(self.addons.exists())

    def test_changed_archive_rejected(self):
        self.archive.write_bytes(b'changed')
        with self.assertRaises(ValueError):install_addon(self.root,self.addons)
        self.assertFalse(self.addons.exists())

    def test_no_service_desktop_activation_only_writes_owned_metadata(self):
        with patch('integrations.subprocess.run') as run:
            result=activate(self.root,self.addons,enable_service=False,desktop=False)
        run.assert_not_called()
        self.assertEqual(result['status'],'activated')

    def test_stop_rejects_foreign_service(self):
        atomic_json(self.root/'integration.json',{'unit_name':'unrelated.service'})
        with patch('integrations.subprocess.run') as run:
            with self.assertRaises(ValueError):stop_owned_service(self.root)
        run.assert_not_called()

    def test_renderer_targets_installed_runtime(self):
        from runtime_config import load_config
        from runtime_cli import render_service
        config=load_config(self.root/'config/runtime.json')
        unit=render_service(config,self.root/'runtime/server.py')
        self.assertIn(str(self.root/'runtime/server.py'),unit)
        self.assertNotIn(str(ROOT/'src/daemon/server.py'),unit)


if __name__=='__main__':unittest.main()
