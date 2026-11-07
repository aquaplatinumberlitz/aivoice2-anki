"""Source discovery has no voice-count whitelist; new dialects are explicit."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/setup'))
from voice_sources import scan_voicebanks,prepare_voice_import,parse_dialects,default_language


class VoiceSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.voices=self.root/'Voice';self.voices.mkdir()
        self.lang=self.root/'Lang';(self.lang/'standard').mkdir(parents=True)
        (self.lang/'standard/standard.aildic').write_bytes(b'fixture')

    def bank(self,name,metadata='infox.bin'):
        folder=self.voices/name;folder.mkdir()
        for file in [name+'.aivdic','voice.lic',metadata,'images.dat']:(folder/file).write_bytes(b'fixture')
        return folder

    def test_arbitrary_count_and_legacy_metadata(self):
        for i in range(35):self.bank('NewBank_'+str(i),metadata='info.bin' if i%2 else 'infox.bin')
        items=scan_voicebanks(self.voices,{})
        self.assertEqual(len(items),35)
        self.assertTrue(all(item['files_ready'] for item in items))
        self.assertTrue(all(item['language']=='standard' for item in items))

    def test_new_voice_automatically_uses_standard_and_is_importable(self):
        self.bank('BrandNewVoice')
        files,langs,registry,catalog=prepare_voice_import(self.voices,self.lang,['BrandNewVoice'],{})
        self.assertEqual(len(files),4);self.assertEqual(len(langs),1)
        self.assertEqual(registry['BrandNewVoice']['language'],'standard')
        self.assertIn('BrandNewVoice',catalog)

    def test_akane_family_policy_is_case_insensitive_and_covers_future_banks(self):
        for name in ['KotonohaAkane_ns_48','akane_west_emo_48','AkaneNewVoice_99']:
            self.assertEqual(default_language(name),'kansai')
        for name in ['KizunaAkari_ns_48','NewVoice_99','Galaco_ns_st_48']:
            self.assertEqual(default_language(name),'standard')

    def test_missing_files_and_symlink_are_reported(self):
        folder=self.bank('Incomplete');(folder/'voice.lic').unlink()
        self.assertIn('Thiếu voice.lic',scan_voicebanks(self.voices,{})[0]['issues'])
        with self.assertRaises(ValueError):prepare_voice_import(self.voices,self.lang,['Incomplete'],{}, {'Incomplete':'standard'})
        (folder/'voice.lic').symlink_to(folder/'images.dat')
        self.assertFalse(scan_voicebanks(self.voices,{})[0]['files_ready'])

    def test_canonical_package_wins_over_extra_package(self):
        folder=self.bank('Bank');(folder/'Other.aivdic').write_bytes(b'fixture')
        self.assertEqual(scan_voicebanks(self.voices,{})[0]['package'],'Bank.aivdic')

    def test_cli_override_validation(self):
        self.assertEqual(parse_dialects(['New=standard']),{'New':'standard'})
        for value in ['New','New=automatic','=standard','New=../standard']:
            with self.assertRaises(ValueError):parse_dialects([value])


if __name__=='__main__':unittest.main()
