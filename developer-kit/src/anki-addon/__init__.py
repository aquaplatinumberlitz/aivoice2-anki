from __future__ import annotations

import hashlib
from html import unescape
import io
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import wave
from types import SimpleNamespace

from aqt import gui_hooks, mw
from aqt.qt import (QAction, QComboBox, QDialog, QHBoxLayout, QLabel, Qt,
                    QPushButton, QTextEdit, QVBoxLayout)
from aqt.operations.note import update_note
from aqt.reviewer import Reviewer
from aqt.sound import av_player
from .card_model import ensure_model, MODEL_NAME
from . import editor_compat

DEFAULT_VOICE = 'KotonohaAkane_ns_48/KotonohaAkane_ns_48'
_dialogs = set()


def config():
    return mw.addonManager.getConfig(__name__) or {}


def request(path, payload=None):
    base = str(config().get('api_url', 'http://127.0.0.1:17862')).rstrip('/')
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(base + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode('utf-8', errors='replace')
        try:
            detail = json.loads(detail).get('error', detail)
        except (ValueError, AttributeError):
            pass
        raise RuntimeError(str(detail)) from None
    except urllib.error.URLError:
        raise RuntimeError('Không kết nối được A.I.VOICE2. Chạy: systemctl --user start aivoice2-tts') from None


def plain_text(value):
    value = re.sub(r'\[sound:[^\]]+\]', '', value)
    value = re.sub(r'(?is)<(script|style|rt|rp)\b[^>]*>.*?</\1>', '', value)
    value = re.sub(r'(?i)<br\s*/?>|</(?:div|p|li)>', '\n', value)
    value = unescape(re.sub(r'<[^>]*>', '', value))
    value = re.sub(r'\{\{c\d+::(.*?)(?:::[^{}]*)?\}\}', r'\1', value)
    return value.strip()


class SpeechDialog(QDialog):
    def __init__(self, editor=None, note_info=None, note_id=None, initial_text=None, auto_play=False):
        super().__init__(editor.parentWindow if editor else mw)
        self.setWindowTitle('A.I.VOICE2')
        self.setModal(True)
        self.resize(640, 360)
        self.editor = editor
        self.note_info = note_info
        self.note_id = note_id
        self.auto_play = auto_play
        if note_id is not None:
            note = mw.col.get_note(note_id)
            note_info = self.note_info = SimpleNamespace(id=note.id, mid=note.mid, fields=note.fields[:])
        self.audio = None
        self.filename = None
        self.audio_signature = None
        self.busy = False
        self.alive = True
        self.finished.connect(self.on_closed)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Nội dung tiếng Nhật:'))
        self.text = QTextEdit()
        self.text.setAcceptRichText(False)
        layout.addWidget(self.text)
        row = QHBoxLayout()
        row.addWidget(QLabel('Giọng:'))
        self.voice = QComboBox()
        row.addWidget(self.voice, 1)
        self.refresh = QPushButton('Làm mới')
        self.refresh.clicked.connect(self.load_voices)
        row.addWidget(self.refresh)
        layout.addLayout(row)
        self.target = QComboBox()
        self.field_names = []
        if note_info:
            model = mw.col.models.get(note_info.mid)
            self.field_names = [field['name'] for field in model['flds']]
            self.target.addItems(self.field_names)
            source = editor.last_field_index if editor else 0
            if source is None or source >= len(note_info.fields):
                source = 0
            field_name = config().get('source_field', '')
            if field_name in self.field_names:
                source = self.field_names.index(field_name)
            self.text.setPlainText(plain_text(note_info.fields[source]))
            preferred = str(config().get('audio_field', '')).lower()
            targets = [i for i, name in enumerate(self.field_names)
                       if name.lower() in ([preferred] if preferred else ['audio', 'sound', '音声'])]
            self.target.setCurrentIndex(targets[0] if targets else source)
            target_row = QHBoxLayout()
            target_row.addWidget(QLabel('Field lưu audio:'))
            target_row.addWidget(self.target, 1)
            layout.addLayout(target_row)
        else:
            self.text.setPlainText('こんにちは。これは音声のテストです。')
        if initial_text:
            self.text.setPlainText(initial_text)
        self.status = QLabel('Đang tải danh sách giọng…')
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.play = QPushButton('🔊 Phát thử')
        self.play.setDefault(True)
        self.play.clicked.connect(self.speak)
        buttons.addWidget(self.play)
        self.insert = QPushButton('Đồng ý · Chèn vào card')
        self.insert.setVisible(note_info is not None)
        self.insert.clicked.connect(self.insert_audio)
        buttons.addWidget(self.insert)
        buttons.addStretch()
        close = QPushButton('Đóng')
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.text.textChanged.connect(self.invalidate_audio)
        self.voice.currentIndexChanged.connect(self.invalidate_audio)
        self.load_voices()

    def on_closed(self, _result):
        self.alive = False
        _dialogs.discard(self)

    def signature(self):
        return self.text.toPlainText().strip(), self.voice.currentData()

    def update_buttons(self):
        self.play.setEnabled(not self.busy and bool(self.voice.currentData()))
        self.refresh.setEnabled(not self.busy)
        self.insert.setEnabled(not self.busy and self.audio is not None
                               and self.signature() == self.audio_signature)

    def invalidate_audio(self, *_args):
        self.update_buttons()

    def load_voices(self):
        self.busy = True
        preferred = self.voice.currentData() or config().get('voice', DEFAULT_VOICE)
        self.update_buttons()

        def done(future):
            if not self.alive:
                return
            self.busy = False
            try:
                result = json.loads(future.result())
                self.voice.clear()
                for item in result['voices']:
                    self.voice.addItem(f'{item["name"]} — {item["folder"]}', item['id'])
                index = self.voice.findData(preferred)
                self.voice.setCurrentIndex(index if index >= 0 else 0)
                self.status.setText(f'Sẵn sàng · {self.voice.count()} giọng')
            except Exception as error:
                self.status.setText(str(error))
            self.update_buttons()
            if self.auto_play and self.voice.count():
                self.auto_play = False
                self.speak()

        mw.taskman.run_in_background(lambda: request('/v1/voices'), done, uses_collection=False)

    def speak(self):
        signature = self.signature()
        if self.busy:
            return
        if not signature[0]:
            self.status.setText('Nhập nội dung cần đọc.')
            return
        self.busy = True
        self.status.setText('Đang tạo âm thanh…')
        self.update_buttons()
        started = time.monotonic()

        def done(future):
            if not self.alive:
                return
            self.busy = False
            if self.signature() != signature:
                self.status.setText('Nội dung hoặc giọng đã đổi. Bấm phát để tạo lại.')
                self.update_buttons()
                return
            try:
                data = future.result()
                with wave.open(io.BytesIO(data), 'rb') as wav:
                    duration = wav.getnframes() / wav.getframerate()
                    if wav.getsampwidth() != 2 or wav.getnchannels() != 1 or duration <= 0:
                        raise ValueError('Audio trả về không hợp lệ')
                filename = 'aivoice2_' + hashlib.sha256(data).hexdigest() + '.wav'
                folder = Path.home() / '.cache' / 'aivoice2-anki'
                folder.mkdir(parents=True, exist_ok=True)
                path = folder / filename
                path.write_bytes(data)
                self.audio = data
                self.filename = filename
                self.audio_signature = signature
                av_player.play_file(str(path))
                self.status.setText(f'Đang phát · audio {duration:.1f}s · tạo trong {time.monotonic() - started:.1f}s')
                cfg = config()
                cfg['voice'] = signature[1]
                mw.addonManager.writeConfig(__name__, cfg)
            except Exception as error:
                self.status.setText(str(error))
            self.update_buttons()

        mw.taskman.run_in_background(
            lambda: request('/v1/speak', {'text': signature[0], 'voice': signature[1]}),
            done, uses_collection=False)

    def insert_audio(self):
        if not self.note_info or self.audio is None or self.signature() != self.audio_signature:
            return
        index = self.target.currentIndex()
        if self.note_id is not None:
            try:
                note = mw.col.get_note(self.note_id)
                if note.mid != self.note_info.mid:
                    raise ValueError('Loại note đã thay đổi; mở lại hộp thoại.')
                filename = mw.col.media.write_data(self.filename, self.audio)
                tag = f'[sound:{filename}]'
                if tag not in note.fields[index]:
                    note.fields[index] += tag
                self.busy = True
                self.update_buttons()

                def saved(_changes):
                    if self.alive:
                        self.busy = False
                        self.status.setText(f'Đã lưu audio vào {self.field_names[index]}.')
                        self.update_buttons()

                def failed(error):
                    if self.alive:
                        self.busy = False
                        self.status.setText(str(error))
                        self.update_buttons()

                update_note(parent=mw, note=note).success(saved).failure(failed).run_in_background()
            except Exception as error:
                self.status.setText(str(error))
            return

        def insert(info):
            if not self.alive:
                return
            if info.id != self.note_info.id or info.mid != self.note_info.mid:
                self.status.setText('Note đã thay đổi; mở lại A.I.VOICE2 từ note cần lưu.')
                return
            try:
                filename = mw.col.media.write_data(self.filename, self.audio)
                tag = f'[sound:{filename}]'
                fields = info.fields[:]
                if tag not in fields[index]:
                    fields[index] += tag
                self.busy = True
                self.update_buttons()

                def saved():
                    if self.alive:
                        self.busy = False
                        self.status.setText(f'Đã chèn audio vào {self.field_names[index]}.')
                        self.update_buttons()

                def failed(error):
                    if self.alive:
                        self.busy = False
                        self.status.setText(str(error))
                        self.update_buttons()

                editor_compat.set_fields(self.editor, fields, self.field_names, saved, failed)
            except Exception as error:
                self.status.setText(str(error))

        editor_compat.note_info(self.editor, insert)


def show_dialog(editor=None, *, note_id=None, initial_text=None, auto_play=None):
    if editor and initial_text is None:
        initial_text = editor.web.page().selectedText().strip() or None
    def open_dialog(info=None):
        dialog = SpeechDialog(editor, info, note_id=note_id, initial_text=initial_text,
                              auto_play=bool(initial_text) if auto_play is None else auto_play)
        _dialogs.add(dialog)
        dialog.show()
    if editor:
        editor_compat.note_info(editor, open_dialog)
    else:
        open_dialog()


def editor_buttons(buttons, editor):
    buttons.append(editor.addButton(
        icon=None, cmd='aivoice2Speak', func=show_dialog,
        tip='A.I.VOICE2: nghe phần tiếng Nhật được chọn (Ctrl+Shift+V)', label='🎙 AI',
        keys='Ctrl+Shift+V'))


action = QAction('A.I.VOICE2 — Phát thử…', mw)
action.triggered.connect(lambda _checked=False: show_dialog())
mw.form.menuTools.addAction(action)
gui_hooks.editor_did_init_buttons.append(editor_buttons)

SELECTION_SCRIPT = (Path(__file__).parent / 'selection.js').read_text(encoding='utf-8')


def reviewer_selection(card):
    mw.reviewer.web.eval(SELECTION_SCRIPT.replace('__AIVOICE_NOTE_ID__', str(int(card.nid))))


def editor_selection(editor):
    if editor.web:
        editor.web.eval(SELECTION_SCRIPT.replace('__AIVOICE_NOTE_ID__', str(int(editor_compat.note_id(editor) or 0))))


def selection_message(handled, message, context):
    prefix = 'aivoice2:selection:'
    if not message.startswith(prefix):
        return handled
    try:
        data = json.loads(message[len(prefix):])
        text = str(data['text']).strip()
        if not text or len(text) > 4096:
            return True, None
        if isinstance(context, Reviewer):
            if context.card and int(context.card.nid) == int(data['noteId']):
                show_dialog(note_id=context.card.nid, initial_text=text)
        elif callable(getattr(context, 'get_note_info', None)) or hasattr(context, 'note'):
            show_dialog(context, initial_text=text)
    except (ValueError, KeyError, TypeError):
        pass
    return True, None


gui_hooks.reviewer_did_show_question.append(reviewer_selection)
gui_hooks.reviewer_did_show_answer.append(reviewer_selection)
gui_hooks.editor_did_load_note.append(editor_selection)
gui_hooks.webview_did_receive_js_message.append(selection_message)


def prepare_model():
    ensure_model(mw.col)


def show_model_help():
    from aqt.utils import showInfo
    prepare_model()
    showInfo(f'Đã có loại note “{MODEL_NAME}”.\n\n'
             'Trong Add, chọn loại note này và nhập Japanese, Romaji, Vietnamese.\n'
             'Khi học: bôi đen tiếng Nhật → 🎙 Nghe thử → Phát thử.\n'
             'Nếu đồng ý, bấm “Chèn vào card” để lưu vào Audio.', parent=mw)


model_action = QAction('A.I.VOICE2 — Mẫu card Nhật–Việt', mw)
model_action.triggered.connect(lambda _checked=False: show_model_help())
mw.form.menuTools.addAction(model_action)
gui_hooks.profile_did_open.append(prepare_model)


def close_dialogs():
    for dialog in list(_dialogs):
        dialog.reject()


gui_hooks.profile_will_close.append(close_dialogs)
