"""Voice maintenance transaction and runtime lock checks using disposable fixtures."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/setup'))
from install_core import atomic_json,sha
from runtime_config import acquire_runtime_lease,load_config,ConfigError
from voice_manager import add_voices,remove_voice,restore_voice,maintenance


class VoiceManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'install'
        (self.root/'app/Voice/Aoi').mkdir(parents=True)
        (self.root/'app/Voice/Aoi/Aoi.aivdic').write_bytes(b'aoi')
        (self.root/'app/Voice/Aoi/voice.lic').write_bytes(b'fixture')
        (self.root/'app/Lang/standard').mkdir(parents=True)
        (self.root/'app/Lang/standard/standard.aildic').write_bytes(b'lang')
        atomic_json(self.root/'config/runtime.json',dict(schema_version=1,app_dir='../app',runtime_dir='../runtime',
            engine_prefix='../prefixes/engine',gui_prefix='../prefixes/gui',voice_registry='../voices.json',default_voice='Aoi/Aoi'))
        atomic_json(self.root/'voices.json',{'schema_version':1,'voices':{'Aoi':{'language':'standard'},'Akane':{'language':'kansai'}}})
        atomic_json(self.root/'install-manifest.json',{'schema_version':1,'selected_voices':['Aoi'],'files':{}})
        self.source=self.base/'source';(self.source/'voices/Akane').mkdir(parents=True)
        (self.source/'Lang/kansai').mkdir(parents=True)
        (self.source/'voices/Akane/Akane.aivdic').write_bytes(b'akane')
        (self.source/'voices/Akane/voice.lic').write_bytes(b'fixture')
        (self.source/'voices/Akane/info.bin').write_bytes(b'fixture')
        (self.source/'voices/Akane/images.dat').write_bytes(b'fixture')
        (self.source/'Lang/kansai/kansai.aildic').write_bytes(b'kansai')
        def rec(p,relative,source):return dict(path=relative,bytes=p.stat().st_size,sha256=sha(p),source=source)
        records=[rec(p,p.relative_to(self.source/'voices').as_posix(),'company-voicebanks') for p in (self.source/'voices').rglob('*') if p.is_file()]
        records += [rec(p,p.relative_to(self.source/'Lang').as_posix(),'company-language') for p in (self.source/'Lang').rglob('*') if p.is_file()]
        atomic_json(self.root/'release-inputs.json',{'supported_voice_candidates':[{'folder':'Aoi','language':'standard'},{'folder':'Akane','language':'kansai'}],'files':records})
        self.proc=patch('voice_manager.foreign_running_processes',return_value=[]);self.proc.start();self.addCleanup(self.proc.stop)

    def add(self):add_voices(self.root,self.source/'voices',self.source/'Lang',['Akane'])

    def test_add_remove_default_restore_and_keep_media(self):
        media=self.base/'anki-media/sound.wav';media.parent.mkdir();media.write_bytes(b'keep')
        self.add()
        config=self.root/'config/runtime.json';data=json.loads(config.read_text());data['default_voice']='Akane/Akane';atomic_json(config,data)
        token=remove_voice(self.root,'Akane')
        self.assertFalse((self.root/'app/Voice/Akane').exists())
        self.assertEqual(json.loads(config.read_text())['default_voice'],'Aoi/Aoi')
        restore_voice(self.root,token)
        self.assertEqual((self.root/'app/Voice/Akane/Akane.aivdic').read_bytes(),b'akane')
        self.assertEqual(media.read_bytes(),b'keep')

    def test_last_voice_duplicate_and_missing_source_are_refused(self):
        with self.assertRaises(ValueError):remove_voice(self.root,'Aoi')
        with self.assertRaises(ValueError):add_voices(self.root,self.source/'voices',self.source/'Lang',['unknown'])
        self.add()
        with self.assertRaises(ValueError):self.add()

    def test_runtime_and_maintenance_exclude_each_other(self):
        config=load_config(self.root/'config/runtime.json')
        lease=acquire_runtime_lease(config)
        try:
            with self.assertRaises(ValueError):
                with maintenance(self.root,config):pass
        finally:lease.close()
        with maintenance(self.root,config):
            with self.assertRaises(ConfigError):acquire_runtime_lease(config)

    def test_failed_copy_rolls_back_partial_languages_and_voice(self):
        with patch('voice_manager.refresh_manifest',side_effect=OSError('simulated manifest failure')):
            with self.assertRaises(OSError):self.add()
        self.assertFalse((self.root/'app/Voice/Akane').exists())
        self.assertFalse((self.root/'app/Lang/kansai/kansai.aildic').exists())
        self.assertEqual(json.loads((self.root/'install-manifest.json').read_text())['selected_voices'],['Aoi'])

    def test_tampered_backup_is_not_restored(self):
        self.add();token=remove_voice(self.root,'Akane')
        (self.root/'backups/voices'/token/'Akane/Akane.aivdic').write_bytes(b'changed')
        with self.assertRaises(ValueError):restore_voice(self.root,token)
        self.assertFalse((self.root/'app/Voice/Akane').exists())

    def test_add_new_voice_outside_baseline_and_restore(self):
        source=self.source/'voices/BrandNewVoice';source.mkdir()
        for name in ['BrandNewVoice.aivdic','voice.lic','infox.bin','images.dat']:
            (source/name).write_bytes(b'fixture')
        add_voices(self.root,self.source/'voices',self.source/'Lang',['BrandNewVoice'])
        registry=json.loads((self.root/'voices.json').read_text())['voices']
        self.assertEqual(registry['BrandNewVoice']['language'],'standard')
        token=remove_voice(self.root,'BrandNewVoice')
        restore_voice(self.root,token)
        self.assertTrue((self.root/'app/Voice/BrandNewVoice/BrandNewVoice.aivdic').is_file())


if __name__=='__main__':unittest.main()
