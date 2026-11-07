"""Qt behavior checks for source selection, bounded lists, progress and launch actions."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/setup'))
try:
    from desktop_ui import ManagerWindow,VoiceTable,AddVoicesDialog,PreviewDialog,Picker,STYLE
    from qt_compat import QtWidgets as W,QtCore,Signal
    QT_AVAILABLE=True
except ImportError:QT_AVAILABLE=False


@unittest.skipUnless(QT_AVAILABLE,'Qt 6 not installed in this test environment')
class DesktopUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=W.QApplication.instance() or W.QApplication([])
        cls.app.setStyleSheet(STYLE)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.window=ManagerWindow(ROOT/'build/payload',ROOT/'release/release-inputs.json')
        self.addCleanup(self.window.close)

    def wait_until(self,condition,seconds=3):
        deadline=time.monotonic()+seconds
        while not condition():
            self.app.processEvents();time.sleep(.005)
            if time.monotonic()>deadline:self.fail('Qt event did not complete')

    def test_voice_search_selection_and_installed_filter(self):
        table=VoiceTable()
        table.populate([{'folder':'Akane','label':'Akane','files_ready':True},
                        {'folder':'Aoi','label':'Aoi','files_ready':True},
                        {'folder':'Broken','label':'Broken','files_ready':False}],installed=['Aoi'])
        self.assertEqual(table.selected(),['Akane'])
        table.search.setText('aoi');self.assertTrue(table.table.isRowHidden(0))
        table.select_visible(True);self.assertEqual(table.selected(),['Akane'])
        table.search.clear();table.select_visible(False);self.assertEqual(table.selected(),[])
        self.assertLessEqual(table.table.maximumHeight(),300)
        table.close()

    def test_progress_finishes_at_100_and_failure_does_not(self):
        finished=[];self.window.task_finished.connect(finished.append)
        self.window.begin_task(lambda report,progress:(progress(35,'Copy'),progress(70,'Check')))
        self.wait_until(lambda:len(finished)==1)
        self.assertEqual(self.window.progress.value(),100)
        def broken(report,progress):progress(30,'Check');raise ValueError('fixture failure')
        with patch('desktop_ui.W.QMessageBox.warning'):
            self.window.begin_task(broken)
            self.wait_until(lambda:len(finished)==2)
        self.assertFalse(finished[-1]);self.assertEqual(self.window.progress.value(),30)

    def test_add_dialog_has_own_source_and_disables_installed_bank(self):
        voices=self.root/'Voice';folder=voices/'FutureVoice';folder.mkdir(parents=True)
        for name in ['FutureVoice.aivdic','voice.lic','info.bin','images.dat']:(folder/name).write_bytes(b'fixture')
        with patch('desktop_ui.QtCore.QSettings.value',return_value=''):
            dialog=AddVoicesDialog(self.window,{},installed=['Existing'])
        dialog.source.setText(str(voices));dialog.scan()
        self.assertEqual(dialog.voices.selected(),['FutureVoice'])
        self.assertEqual(self.window.fields['voicebanks'].text(),'')
        dialog.close()

    def test_picker_uses_desktop_dialog_and_remembers_location(self):
        picker=Picker(self.window)
        with patch('desktop_ui.W.QFileDialog.getExistingDirectory',return_value=str(self.root)), \
             patch.object(picker.settings,'setValue') as save:
            self.assertEqual(picker.directory('Choose voices','fixture'),str(self.root))
            save.assert_called_once_with('folders/fixture',str(self.root))

    def test_open_anki_and_editor_are_separate_scoped_launches(self):
        managed=self.root/'install';(managed/'runtime').mkdir(parents=True)
        (managed/'runtime/runtime_cli.py').write_text('# fixture')
        self.window.root_field.setText(str(managed))
        with patch('desktop_ui.shutil.which',return_value='/usr/bin/anki'), \
             patch('desktop_ui.subprocess.Popen') as launch:
            self.window.open_anki();self.window.open_editor()
        self.assertEqual(launch.call_args_list[0].args[0],['/usr/bin/anki'])
        self.assertEqual(launch.call_args_list[1].args[0][-1],'gui')
        self.assertIn(str(managed/'config/runtime.json'),launch.call_args_list[1].args[0])

    def test_preview_discards_result_when_text_changes_during_synthesis(self):
        root=self.root/'managed';(root/'config').mkdir(parents=True)
        config=dict(schema_version=1,app_dir='../app',runtime_dir='../runtime',
                    engine_prefix='../prefixes/engine',gui_prefix='../prefixes/gui',
                    voice_registry='../registry.json',default_voice='Test/Test')
        (root/'config/runtime.json').write_text(json.dumps(config))
        (root/'registry.json').write_text(json.dumps({'schema_version':1,'voices':{'Test':{'language':'standard'}}}))
        folder=root/'app/Voice/Test';folder.mkdir(parents=True)
        for name in ['Test.aivdic','voice.lic']:(folder/name).write_bytes(b'fixture')
        lang=root/'app/Lang/standard';lang.mkdir(parents=True);(lang/'standard.aildic').write_bytes(b'fixture')
        release=threading.Event();started=threading.Event();plays=[]
        class FakePlayback(QtCore.QObject):
            status=Signal(str);requested=Signal(str)
            def __init__(self,parent):super().__init__(parent)
            def stop(self):pass
            def play(self,path):plays.append(path)
        class FakeEngine:
            def __init__(self,config):pass
            def speak(self,*args):started.set();release.wait(2);return root/'fixture.wav',False,{}
            def stop(self):pass
        with patch('desktop_ui.Playback',FakePlayback),patch('server.Engine',FakeEngine), \
             patch('desktop_ui.urllib.request.urlopen',side_effect=OSError('offline')):
            dialog=PreviewDialog(self.window,root);dialog.speak()
            self.wait_until(started.is_set)
            dialog.text.setPlainText('ありがとう');release.set()
            self.wait_until(lambda:not dialog.busy)
            self.assertEqual(plays,[]);self.assertIsNone(dialog.wav)
            dialog.close()


if __name__=='__main__':unittest.main()
