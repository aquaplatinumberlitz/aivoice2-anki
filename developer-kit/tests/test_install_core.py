"""Installer data-loss guards: rollback before commit, raced destination and symlinks."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/setup'))
import install_core


class InstallCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_atomic_commit_never_overwrites_existing_directory(self):
        stage=self.root/'stage';stage.mkdir();(stage/'file').write_text('new')
        dest=self.root/'existing';dest.mkdir()
        with self.assertRaises(OSError):install_core.commit_directory(stage,dest)
        self.assertTrue((stage/'file').is_file());self.assertEqual(list(dest.iterdir()),[])
        dest.rmdir();install_core.commit_directory(stage,dest)
        self.assertEqual((dest/'file').read_text(),'new')

    def test_input_rejects_symlink_and_path_escape(self):
        (self.root/'file').write_text('fixture')
        (self.root/'link').symlink_to(self.root/'file')
        for name in ['link','../file','/etc/passwd']:
            with self.subTest(name=name),self.assertRaises(ValueError):
                install_core.safe_file(self.root,name)

    def test_existing_destination_does_not_touch_files(self):
        dest=self.root/'existing';dest.mkdir();(dest/'keep').write_text('important')
        baseline=self.root/'baseline.json';baseline.write_text('{}')
        with self.assertRaisesRegex(ValueError,'đã tồn tại'):
            install_core.install_files(self.root/'msi',self.root/'lang',self.root/'voice',
                                       [],dest,self.root/'payload',baseline=baseline)
        self.assertEqual((dest/'keep').read_text(),'important')

    def test_bad_extracted_stock_rolls_back_only_owned_stage(self):
        def record(path,relative):return dict(path=relative,bytes=path.stat().st_size,sha256=install_core.sha(path))
        msi=self.root/'input.msi';msi.write_bytes(b'fixture')
        languages=self.root/'Lang';(languages/'standard').mkdir(parents=True)
        (languages/'standard/standard.aildic').write_bytes(b'lang')
        voicebanks=self.root/'voices';(voicebanks/'Aoi').mkdir(parents=True)
        (voicebanks/'Aoi/Aoi.aivdic').write_bytes(b'voice')
        for name in ['voice.lic','info.bin','images.dat']:(voicebanks/'Aoi'/name).write_bytes(b'fixture')
        payload=self.root/'payload';(payload/'runtime').mkdir(parents=True)
        (payload/'runtime/voice_registry.json').write_text(json.dumps({'voices':{'Aoi':{'language':'standard'}}}))
        baseline=self.root/'baseline.json'
        data={'baseline_id':'fixture','supported_voice_candidates':[{'folder':'Aoi'}],
              'sources':{'original-msi':{'sha256':install_core.sha(msi)}},'files':[
                  dict(source='company-language',**record(languages/'standard/standard.aildic','standard/standard.aildic')),
                  dict(source='company-voicebanks',**record(voicebanks/'Aoi/Aoi.aivdic','Aoi/Aoi.aivdic')),
                  dict(source='msi-extracted-app',path='expected.dll',bytes=1,sha256='invalid')]}
        baseline.write_text(json.dumps(data))
        def extraction(command,**kwargs):
            extracted=Path(command[2])/'ProgramFiles64Folder/AI/AIVoice2/AIVoice2Editor'
            extracted.mkdir(parents=True);(extracted/'expected.dll').write_bytes(b'x')
        dest=self.root/'new-install'
        with patch.object(install_core,'dependency_report',return_value={}), \
             patch.object(install_core,'verify_payload',return_value={'baseline_id':'fixture'}), \
             patch.object(install_core.subprocess,'run',side_effect=extraction):
            with self.assertRaisesRegex(ValueError,'không khớp'):
                install_core.install_files(msi,languages,voicebanks,['Aoi'],dest,payload,baseline)
        self.assertFalse(dest.exists())
        self.assertEqual(list(self.root.glob('.aivoice2-install-*')),[])
        self.assertEqual(msi.read_bytes(),b'fixture')


if __name__=='__main__':unittest.main()
