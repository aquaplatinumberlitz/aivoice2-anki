#!/usr/bin/env python3
"""Real Anki/Qt test in an isolated profile, never opens the user's collection.

Checks selection -> microphone -> automatic preview -> explicit insert, including
that preview alone leaves the note and collection media unchanged.
"""
import json
import argparse
import hashlib
import io
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import traceback
import wave
import faulthandler
faulthandler.enable(all_threads=True)

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--legacy', action='store_true')
parser.add_argument('--api-url', default='http://127.0.0.1:17862')
parser.add_argument('--expected-voices', type=int, default=9)
parser.add_argument('--evidence-dir', type=Path, default=ROOT / 'notes/evidence')
parser.add_argument('--addon-source', type=Path, default=ROOT / 'src/anki-addon')
parser.add_argument('--temp-dir', type=Path)
parser.add_argument('--null-audio',action='store_true',help='Use MPV null audio only in this temporary Anki base')
args = parser.parse_args()
EVIDENCE = args.evidence_dir
EVIDENCE.mkdir(parents=True, exist_ok=True)
LEGACY = args.legacy
REPORT = EVIDENCE / ('anki-gui-legacy.jsonl' if LEGACY else 'anki-gui-smoke.jsonl')
REPORT.write_text('')
BASE = Path(tempfile.mkdtemp(prefix='aivoice2-anki-test-', dir=args.temp_dir))
if args.null_audio:
    (BASE/'mpv.conf').write_text('ao=null\n')
shutil.copytree(args.addon_source, BASE / 'addons21' / 'aivoice2_local',
                ignore=shutil.ignore_patterns('__pycache__', 'install.py'))
addon_config = BASE / 'addons21/aivoice2_local/config.json'
cfg = json.loads(addon_config.read_text())
cfg['api_url'] = args.api_url
addon_config.write_text(json.dumps(cfg))
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['ANKI_SINGLE_INSTANCE_KEY'] = 'aivoice2-test-' + str(os.getpid())

import aqt
from aqt import gui_hooks
from aqt.profiles import ProfileManager
from aqt.qt import QTimer
import anki.lang

anki.lang.set_lang('en_US')
pm = ProfileManager(BASE)
pm.setupMeta()
pm.create('Test')
pm.load('Test')
pm.profile['autoSync'] = False
pm.meta['firstRun'] = False
pm.meta['defaultLang'] = 'en_US'
pm.save()
pm.db.close()

state = {'nid': None, 'selected': False, 'previewed': False, 'done': False}


def record(event, **kw):
    with REPORT.open('a') as f:
        f.write(json.dumps({'event': event, **kw}, ensure_ascii=False) + '\n')
    print(event, kw, flush=True)


def fail(message):
    if state['done']:
        return
    state['done'] = True
    record('failed', detail=message)
    QTimer.singleShot(200, aqt.mw.close)


def poll_dialog():
    try:
        module = sys.modules['aivoice2_local']
        dialogs = list(module._dialogs)
        if not dialogs:
            QTimer.singleShot(200, poll_dialog)
            return
        dialog = dialogs[0]
        if dialog.busy or dialog.audio is None:
            QTimer.singleShot(200, poll_dialog)
            return
        assert dialog.text.toPlainText() == 'こんにちは', dialog.text.toPlainText()
        assert dialog.voice.count() == args.expected_voices, dialog.voice.count()
        with wave.open(io.BytesIO(dialog.audio)) as audio:
            assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, 48000)
            assert audio.getnframes() > 0
        state['preview_audio'] = dialog.audio
        record('preview_wav_valid', sha256=hashlib.sha256(dialog.audio).hexdigest(),
               voice=dialog.voice.currentData(), text=dialog.text.toPlainText())
        assert aqt.mw.col.get_note(state['nid'])['Audio'] == ''
        assert not list(Path(aqt.mw.col.media.dir()).glob('aivoice2_*.wav'))
        if not state.get('stale_checked'):
            # A slow response must not start playing after the user edits text.
            # Reuse a valid WAV so this checks request identity, not WAV parsing.
            original_request=module.request;preview=dialog.audio
            def delayed_request(path,payload=None):
                if path=='/v1/speak':time.sleep(.35);return preview
                return original_request(path,payload)
            state.update(stale_request=original_request,stale_player_count=state.get('playback_count',0),dialog=dialog)
            module.request=delayed_request;dialog.audio=None;dialog.speak()
            dialog.text.setPlainText('ありがとう')
            QTimer.singleShot(100,check_stale_preview)
            return
        record('preview_did_not_modify_note_or_media')
        dialog.grab().save(str(EVIDENCE / 'anki-dialog.png'))
        assert dialog.target.currentText() == 'Audio'
        assert dialog.insert.isEnabled()
        state['dialog'] = dialog
        dialog.insert.click()
        QTimer.singleShot(400, check_insert)
    except Exception:
        fail(traceback.format_exc())


def check_stale_preview():
    try:
        dialog=state['dialog']
        if dialog.busy:
            QTimer.singleShot(100,check_stale_preview);return
        assert dialog.audio is None,'Stale response was accepted'
        assert state.get('playback_count',0)==state['stale_player_count'],'Stale response started playback'
        assert aqt.mw.col.get_note(state['nid'])['Audio']==''
        module=sys.modules['aivoice2_local'];module.request=state['stale_request']
        state['stale_checked']=True
        record('changed_text_discarded_stale_preview')
        dialog.text.setPlainText('こんにちは');dialog.speak()
        QTimer.singleShot(200,poll_dialog)
    except Exception:fail(traceback.format_exc())


def check_insert():
    try:
        dialog = state['dialog']
        if dialog.busy:
            QTimer.singleShot(200, check_insert)
            return
        note = aqt.mw.col.get_note(state['nid'])
        assert note['Japanese'] == 'こんにちは。今日はいい天気ですね。'
        assert note['Romaji'] == 'Konnichiwa. Kyou wa ii tenki desu ne.'
        assert note['Vietnamese'] == 'Xin chào. Hôm nay thời tiết đẹp nhỉ.'
        assert note['Audio'].startswith('[sound:aivoice2_'), note['Audio']
        filename = note['Audio'][7:-1]
        assert (Path(aqt.mw.col.media.dir()) / filename).is_file()
        assert (Path(aqt.mw.col.media.dir()) / filename).read_bytes() == state['preview_audio']
        record('explicit_insert_saved_audio', tag=note['Audio'])
        dialog.insert.click()
        QTimer.singleShot(400, check_duplicate)
    except Exception:
        fail(traceback.format_exc())


def check_duplicate():
    try:
        if state['dialog'].busy:
            QTimer.singleShot(200, check_duplicate)
            return
        assert aqt.mw.col.get_note(state['nid'])['Audio'].count('[sound:') == 1
        record('duplicate_insert_did_not_duplicate_tag')
        state['dialog'].reject()
        from aqt.addcards import AddCards, NewAddCards
        window = AddCards(aqt.mw) if LEGACY else NewAddCards(aqt.mw)
        state['editor_window'] = window
        model = sys.modules['aivoice2_local'].ensure_model(aqt.mw.col)
        if LEGACY:
            window.editor.set_note(aqt.mw.col.new_note(model), focusTo=0)
        else:
            window.load_new_note(notetype_id=model['id'])
        record('editor_created', editor=type(window.editor).__name__, legacy=LEGACY)
        QTimer.singleShot(1800, prepare_editor)
    except Exception:
        fail(traceback.format_exc())


def prepare_editor():
    editor = state['editor_window'].editor
    fields = ['今日はいい天気ですね。', 'Kyou wa ii tenki desu ne.', 'Hôm nay trời đẹp nhỉ.', '']
    names = ['Japanese', 'Romaji', 'Vietnamese', 'Audio']
    if LEGACY:
        editor.note.fields = fields
        editor.loadNote(focusTo=0)
    else:
        script = f'setFields({json.dumps(names)}, {json.dumps(fields)}); saveNow();'
        editor.web.eval(script)
    module = sys.modules['aivoice2_local']
    QTimer.singleShot(500, lambda: module.show_dialog(editor, initial_text='こんにちは'))
    QTimer.singleShot(800, poll_editor)


def poll_editor():
    try:
        dialogs = list(sys.modules['aivoice2_local']._dialogs)
        if not dialogs or dialogs[0].busy or dialogs[0].audio is None:
            QTimer.singleShot(200, poll_editor)
            return
        dialog = dialogs[0]
        assert dialog.target.currentText() == 'Audio'
        state['editor_dialog'] = dialog
        dialog.insert.click()
        QTimer.singleShot(600, check_editor)
    except Exception:
        fail(traceback.format_exc())


def check_editor():
    if state['editor_dialog'].busy:
        QTimer.singleShot(200, check_editor)
        return
    def inspect(info):
        try:
            assert info.fields[0] == '今日はいい天気ですね。', info.fields
            assert info.fields[1] == 'Kyou wa ii tenki desu ne.'
            assert info.fields[2] == 'Hôm nay trời đẹp nhỉ.'
            assert info.fields[3].startswith('[sound:aivoice2_'), info.fields
            record('editor_insert_preserved_other_fields', fields=info.fields)
            assert state['previewed']
            state['editor_dialog'].reject()
            state['editor_window'].editor.cleanup()
            state['editor_window'].hide()
            state['editor_window'].deleteLater()
            QTimer.singleShot(300, prepare_existing_editor)
        except Exception:
            fail(traceback.format_exc())
    sys.modules['aivoice2_local'].editor_compat.note_info(state['editor_window'].editor, inspect)


def prepare_existing_editor():
    try:
        from aqt.qt import QDialog, QWidget, QVBoxLayout
        from aqt.editor import Editor, NewEditor, EditorMode
        window = QDialog(aqt.mw)
        layout = QVBoxLayout(window)
        widget = QWidget(window)
        layout.addWidget(widget)
        editor_class = Editor if LEGACY else NewEditor
        editor = editor_class(aqt.mw, widget, window, editor_mode=EditorMode.EDIT_CURRENT)
        state['existing_window'] = window
        state['existing_editor'] = editor
        note = aqt.mw.col.get_note(state['nid'])
        note['Audio'] = ''
        aqt.mw.col.update_note(note)
        editor.set_note(note, focusTo=0)
        window.show()
        QTimer.singleShot(1000, lambda: sys.modules['aivoice2_local'].show_dialog(
            editor, initial_text='こんにちは'))
        QTimer.singleShot(1500, poll_existing_editor)
    except Exception:
        fail(traceback.format_exc())


def poll_existing_editor():
    try:
        dialogs = list(sys.modules['aivoice2_local']._dialogs)
        if not dialogs or dialogs[0].busy or dialogs[0].audio is None:
            QTimer.singleShot(200, poll_existing_editor)
            return
        state['existing_dialog'] = dialogs[0]
        dialogs[0].insert.click()
        QTimer.singleShot(600, check_existing_editor)
    except Exception:
        fail(traceback.format_exc())


def check_existing_editor():
    try:
        if state['existing_dialog'].busy:
            QTimer.singleShot(200, check_existing_editor)
            return
        note = aqt.mw.col.get_note(state['nid'])
        assert note['Audio'].startswith('[sound:aivoice2_'), note.fields
        assert note['Japanese'] == 'こんにちは。今日はいい天気ですね。'
        assert note['Romaji'] == 'Konnichiwa. Kyou wa ii tenki desu ne.'
        assert note['Vietnamese'] == 'Xin chào. Hôm nay thời tiết đẹp nhỉ.'
        record('existing_editor_persisted_audio', legacy=LEGACY)
        state['existing_dialog'].reject()
        state['existing_editor'].cleanup()
        state['existing_window'].hide()
        state['existing_window'].deleteLater()
        state['done'] = True
        record('passed')
        from aqt.sound import av_player
        av_player.stop_and_clear_queue()
        aqt.mw.moveToState('deckBrowser')
        QTimer.singleShot(700, aqt.mw.close)
    except Exception:
        fail(traceback.format_exc())


def playback(player, tag):
    filename = getattr(tag, 'filename', '')
    if 'aivoice2_' in filename:
        state['playback_count']=state.get('playback_count',0)+1
        state['previewed'] = True
        record('anki_playback_started', player=type(player).__name__, path=filename)


def question(card):
    if card.nid != state['nid'] or state['selected']:
        return
    state['selected'] = True
    script = '''(() => {
      const el = document.querySelector('.aivoice-japanese');
      const range = document.createRange();
      range.setStart(el.firstChild, 0); range.setEnd(el.firstChild, 5);
      const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
      document.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
      setTimeout(() => document.querySelector('#aivoice2-selection-mic').click(), 100);
    })();'''
    QTimer.singleShot(400, lambda: aqt.mw.reviewer.web.eval(script))
    QTimer.singleShot(1000, poll_dialog)


def opened():
    def prepare():
        try:
            module = sys.modules['aivoice2_local']
            model = module.ensure_model(aqt.mw.col)
            assert [f['name'] for f in model['flds']] == ['Japanese', 'Romaji', 'Vietnamese', 'Audio']
            assert module.ensure_model(aqt.mw.col)['id'] == model['id']
            note = aqt.mw.col.new_note(model)
            note['Japanese'] = 'こんにちは。今日はいい天気ですね。'
            note['Romaji'] = 'Konnichiwa. Kyou wa ii tenki desu ne.'
            note['Vietnamese'] = 'Xin chào. Hôm nay thời tiết đẹp nhỉ.'
            did = aqt.mw.col.decks.id('A.I.VOICE2 Test')
            aqt.mw.col.add_note(note, did)
            state['nid'] = note.id
            aqt.mw.col.decks.select(did)
            aqt.mw.moveToState('review')
            record('test_profile_ready', profile=str(BASE), note_id=note.id)
        except Exception:
            fail(traceback.format_exc())
    QTimer.singleShot(1000, prepare)


gui_hooks.profile_did_open.append(opened)
gui_hooks.reviewer_did_show_question.append(question)
gui_hooks.av_player_did_begin_playing.append(playback)
app = aqt._run(['anki', '--base', str(BASE), '--profile', 'Test'], exec=False)
QTimer.singleShot(90000, lambda: fail('Timed out waiting for GUI flow'))
app.exec()
if not state['done']:
    record('failed', detail='Anki closed before the test completed')
sys.exit(0 if '"event": "passed"' in REPORT.read_text() else 1)
