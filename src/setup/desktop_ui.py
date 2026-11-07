"""Qt desktop UI for install, voice management and audible TTS previews."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import urllib.request
import wave

from qt_compat import QtCore,QtGui,QtWidgets as W,Qt,Signal,QT_BINDING
from install_core import RUNTIME,ROOT,install_files,initialize_runtime
from runtime_config import load_config,load_voice_registry
from voice_sources import scan_voicebanks,VOICE_LABELS

STYLE='''
QWidget { font-family: "Noto Sans", "DejaVu Sans", sans-serif; font-size: 13px; color: #25334b; }
QMainWindow, QDialog { background: #f3f6fa; }
QFrame#sidebar { background: #152137; border: none; }
QFrame#sidebar QLabel { color: #acb9cf; background: transparent; }
QFrame#sidebar QLabel#brand { color: white; font-size: 21px; font-weight: 700; }
QFrame#sidebar QPushButton { color: #b8c6dc; background: transparent; border: 0; text-align: left; padding: 12px 14px; border-radius: 8px; }
QFrame#sidebar QPushButton:hover { background: #21314c; color: white; }
QFrame#sidebar QPushButton:checked { background: #294055; color: #8ce2d1; font-weight: 600; }
QLabel#eyebrow { color: #718199; font-size: 11px; font-weight: 700; }
QLabel#title { color: #17233b; font-size: 26px; font-weight: 700; }
QLabel#subtitle, QLabel#muted { color: #6b7b91; }
QLabel#cardTitle { font-size: 15px; font-weight: 650; color: #20314a; }
QLabel#badge { color: #087767; background: #e3f5ef; border: 1px solid #c8e8dc; border-radius: 12px; padding: 5px 11px; font-size: 11px; font-weight: 650; }
QFrame#card { background: white; border: 1px solid #dfe6ee; border-radius: 12px; }
QLineEdit, QComboBox, QTextEdit { background: #fff; border: 1px solid #d6dfe9; border-radius: 7px; padding: 8px 10px; selection-background-color: #d9f0e9; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #0c8b79; }
QLineEdit:disabled { color: #8a96a9; background: #f1f4f8; }
QPushButton { background: white; border: 1px solid #d2dce7; border-radius: 7px; padding: 9px 14px; font-weight: 550; }
QPushButton:hover { background: #f2f7fa; border-color: #a7bacb; }
QPushButton:pressed { background: #e7eef4; }
QPushButton:disabled { color: #9ca8b8; background: #f2f4f7; border-color: #e3e8ef; }
QPushButton#primary, QPushButton[primary="true"] { color: white; background: #087f6e; border-color: #087f6e; }
QPushButton#primary:hover, QPushButton[primary="true"]:hover { background: #066b5c; }
QPushButton#primary:disabled, QPushButton[primary="true"]:disabled { background: #b5d7ce; border-color: #b5d7ce; color: white; }
QPushButton#danger { color: #b14242; }
QTableWidget { background: white; border: none; outline: 0; alternate-background-color: #f8fafc; selection-background-color: #e4f2ef; selection-color: #173e38; }
QTableWidget::item { padding: 5px 9px; border-bottom: 1px solid #edf1f6; }
QHeaderView::section { background: #f6f8fb; border: 0; border-bottom: 1px solid #e4eaf2; color: #738199; padding: 9px; font-size: 11px; font-weight: 650; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QProgressBar { border: 0; border-radius: 4px; background: #e5ecf3; min-height: 7px; max-height: 7px; }
QProgressBar::chunk { background: #0b9380; border-radius: 4px; }
QFrame#footer { background: white; border-top: 1px solid #dfe6ee; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QToolButton { border: 0; color: #62768e; padding: 5px; }
QPlainTextEdit { background: #f8fafc; border: 1px solid #e1e8f0; border-radius: 7px; font-size: 11px; }
QToolTip { background: #192b43; color: white; border: none; padding: 5px; }
'''


def label(text,name=None,wrap=False):
    widget=W.QLabel(text)
    if name:widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def button(text,callback=None,primary=False):
    widget=W.QPushButton(text);widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if callback:widget.clicked.connect(callback)
    if primary:widget.setObjectName('primary')
    return widget


def card(title,subtitle=''):
    frame=W.QFrame();frame.setObjectName('card')
    layout=W.QVBoxLayout(frame);layout.setContentsMargins(18,16,18,16);layout.setSpacing(10)
    layout.addWidget(label(title,'cardTitle'))
    if subtitle:layout.addWidget(label(subtitle,'muted',True))
    return frame,layout


class Task(QtCore.QObject):
    reported=Signal(str)
    progressed=Signal(int,str)
    succeeded=Signal(object)
    failed=Signal(str)

    def __init__(self,function):
        super().__init__();self.function=function

    def start(self):
        def run():
            try:result=self.function(self.reported.emit,self.progressed.emit)
            except Exception as error:self.failed.emit(str(error))
            else:self.succeeded.emit(result)
        self.thread=threading.Thread(target=run,daemon=True);self.thread.start()


class Picker:
    """Use native Qt desktop dialogs where available, retaining directory history."""
    def __init__(self,parent):
        self.parent=parent;self.settings=QtCore.QSettings('AIVoice2Local','Manager')

    def directory(self,title,key,current=''):
        start=current or self.settings.value('folders/'+key,str(Path.home()))
        while start and not Path(start).is_dir():
            parent=str(Path(start).parent)
            if parent==start:break
            start=parent
        selected=W.QFileDialog.getExistingDirectory(self.parent,title,str(start),
            W.QFileDialog.Option.ShowDirsOnly)
        if selected:self.settings.setValue('folders/'+key,selected)
        return selected

    def file(self,title,key,pattern,current=''):
        start=current or self.settings.value('folders/'+key,str(Path.home()))
        selected,_=W.QFileDialog.getOpenFileName(self.parent,title,str(start),pattern)
        if selected:self.settings.setValue('folders/'+key,str(Path(selected).parent))
        return selected


class PathField(W.QWidget):
    changed=Signal(str)
    def __init__(self,title,picker,key,file_filter=None,hint='',value=''):
        super().__init__();self.picker=picker;self.key=key;self.file_filter=file_filter;self.title=title
        layout=W.QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(5)
        layout.addWidget(label(title))
        row=W.QHBoxLayout();self.edit=W.QLineEdit(value);self.edit.setObjectName(key)
        self.edit.setPlaceholderText(hint or 'Chọn hoặc dán đường dẫn…')
        row.addWidget(self.edit,1);self.browse=button('Chọn…',self.choose);row.addWidget(self.browse)
        layout.addLayout(row);self.edit.textChanged.connect(self.changed)

    def choose(self):
        current=self.edit.text().strip()
        selected=(self.picker.file(self.title,self.key,self.file_filter,current) if self.file_filter
                  else self.picker.directory(self.title,self.key,current))
        if selected:self.edit.setText(selected)

    def text(self):return self.edit.text().strip()
    def setText(self,value):self.edit.setText(str(value))


def normalize_source(path):
    """Accept either the bank container or its parent installation folder."""
    root=Path(path).expanduser()
    for name in ['voicebanks','Voice']:
        if (root/name).is_dir():return root/name
    return root


class VoiceTable(W.QWidget):
    selection_changed=Signal()
    def __init__(self,checkable=True):
        super().__init__();self.checkable=checkable;self._loading=False
        layout=W.QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(8)
        row=W.QHBoxLayout();self.search=W.QLineEdit();self.search.setPlaceholderText('Tìm giọng theo tên…')
        self.search.setClearButtonEnabled(True);row.addWidget(self.search,1)
        self.filter=W.QComboBox();self.filter.addItems(['Tất cả','Chưa cài','Đã cài']);row.addWidget(self.filter)
        self.filter.setVisible(checkable)
        layout.addLayout(row)
        self.table=W.QTableWidget(0,3 if checkable else 2)
        self.table.setObjectName('voiceTable');self.table.setHorizontalHeaderLabels(
            ['','Giọng','Trạng thái'] if checkable else ['Giọng','Ngôn ngữ'])
        self.table.verticalHeader().hide();self.table.setShowGrid(False);self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(W.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(W.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(39)
        header=self.table.horizontalHeader()
        if checkable:header.setSectionResizeMode(0,W.QHeaderView.ResizeMode.Fixed);self.table.setColumnWidth(0,38)
        header.setSectionResizeMode(1 if checkable else 0,W.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2 if checkable else 1,W.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setMinimumHeight(180);self.table.setMaximumHeight(300)
        layout.addWidget(self.table,1)
        footer=W.QHBoxLayout();self.count=label('Chưa có giọng','muted');footer.addWidget(self.count,1)
        if checkable:
            footer.addWidget(button('Chọn đang lọc',lambda:self.select_visible(True)))
            footer.addWidget(button('Bỏ chọn',lambda:self.select_visible(False)))
        layout.addLayout(footer)
        self.search.textChanged.connect(self.apply_filter);self.filter.currentIndexChanged.connect(self.apply_filter)
        self.table.itemChanged.connect(self.changed)

    def populate(self,items,installed=(),selected=None):
        self._loading=True;self.items=items;self.installed=set(installed)
        self.table.setRowCount(len(items))
        for row,item in enumerate(items):
            present=item['folder'] in self.installed
            selectable=item.get('files_ready',True) and not present
            if self.checkable:
                check=W.QTableWidgetItem();check.setFlags(Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsUserCheckable)
                if not selectable:check.setFlags(Qt.ItemFlag.NoItemFlags)
                checked=selectable and (selected is None or item['folder'] in selected)
                check.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
                self.table.setItem(row,0,check)
            name=W.QTableWidgetItem(item.get('label',VOICE_LABELS.get(item['folder'],item['folder'])))
            name.setData(Qt.ItemDataRole.UserRole,item['folder'])
            name.setToolTip(item['folder']);self.table.setItem(row,1 if self.checkable else 0,name)
            status=('Đã cài' if present else ('Sẵn sàng' if selectable else 'Thiếu file')) if self.checkable else (
                'Kansai' if item.get('language')=='kansai' else 'Standard')
            status_item=W.QTableWidgetItem(status)
            status_item.setToolTip(', '.join(item.get('issues',[])))
            self.table.setItem(row,2 if self.checkable else 1,status_item)
        self._loading=False;self.apply_filter()

    def selected(self):
        if not self.checkable:
            row=self.table.currentRow()
            return [self.table.item(row,0).data(Qt.ItemDataRole.UserRole)] if row>=0 else []
        return [item['folder'] for row,item in enumerate(getattr(self,'items',[]))
                if self.table.item(row,0).checkState()==Qt.CheckState.Checked]

    def select_visible(self,enabled):
        for row in range(self.table.rowCount()):
            item=self.table.item(row,0)
            if not self.table.isRowHidden(row) and item.flags()&Qt.ItemFlag.ItemIsEnabled:
                item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)

    def select_only(self,names):
        for row,item in enumerate(getattr(self,'items',[])):
            self.table.item(row,0).setCheckState(Qt.CheckState.Checked if item['folder'] in names else Qt.CheckState.Unchecked)

    def apply_filter(self,*args):
        query=self.search.text().casefold();mode=self.filter.currentIndex()
        visible=0
        for row,item in enumerate(getattr(self,'items',[])):
            present=item['folder'] in getattr(self,'installed',set())
            hide=(query not in (item.get('label','')+' '+item['folder']).casefold()
                  or mode==1 and present or mode==2 and not present)
            self.table.setRowHidden(row,hide);visible+=not hide
        total=self.table.rowCount()
        self.count.setText(f'Đã chọn {len(self.selected())} / {total} giọng · hiện {visible}' if self.checkable else f'{total} giọng đã cài · hiện {visible}')

    def changed(self,*args):
        if not self._loading:self.apply_filter();self.selection_changed.emit()


class AddVoicesDialog(W.QDialog):
    def __init__(self,parent,registry,installed=()):
        super().__init__(parent);self.setWindowTitle('Thêm giọng');self.resize(800,620)
        self.picker=Picker(self);self.registry=registry;self.installed=installed
        layout=W.QVBoxLayout(self);layout.setContentsMargins(24,22,24,22);layout.setSpacing(12)
        layout.addWidget(label('Thêm giọng vào bản cài','title'))
        layout.addWidget(label('Chọn nguồn riêng tại đây. Những giọng đã cài sẽ không bị chép đè.','muted',True))
        self.source=PathField('Thư mục chứa giọng',self.picker,'add-voices');layout.addWidget(self.source)
        self.languages=PathField('Thư mục Lang',self.picker,'add-languages');layout.addWidget(self.languages)
        self.summary=label('Chọn Voice/ hoặc voicebanks/ để xem các giọng.','muted',True);layout.addWidget(self.summary)
        self.voices=VoiceTable();self.voices.filter.setCurrentIndex(1);layout.addWidget(self.voices,1)
        row=W.QHBoxLayout();row.addStretch();row.addWidget(button('Hủy',self.reject))
        self.add=button('Thêm giọng đã chọn',self.accept,True);self.add.setEnabled(False);row.addWidget(self.add);layout.addLayout(row)
        self.source.changed.connect(self.scan);self.voices.selection_changed.connect(self.refresh)
        self.source.setText(self.picker.settings.value('folders/add-voices',''))

    def scan(self,*args):
        if not self.source.text():return
        source=normalize_source(self.source.text())
        try:items=scan_voicebanks(source,self.registry)
        except OSError as error:self.summary.setText(str(error));return
        if (source.parent/'Lang').is_dir() and not self.languages.text():self.languages.setText(source.parent/'Lang')
        self.voices.populate(items,self.installed)
        self.summary.setText(f'Tìm thấy {len(items)} giọng · Akane dùng Kansai, các giọng khác dùng Standard.')
        self.refresh()

    def refresh(self):self.add.setEnabled(bool(self.voices.selected()))


class Playback(QtCore.QObject):
    status=Signal(str)
    requested=Signal(str)
    def __init__(self,parent):
        super().__init__(parent);self.media=None;self.process=None
        try:
            if QT_BINDING=='PySide6':from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
            else:from PyQt6.QtMultimedia import QMediaPlayer,QAudioOutput
            self.media=QMediaPlayer(self);self.audio=QAudioOutput(self);self.audio.setVolume(1)
            self.media.setAudioOutput(self.audio)
            self.media.errorOccurred.connect(lambda *args:self.status.emit('Đã tạo WAV nhưng phát chưa thành công: '+self.media.errorString()))
            self.media.playbackStateChanged.connect(lambda state:self.status.emit('Đang phát qua thiết bị âm thanh mặc định…')
                if state==QMediaPlayer.PlaybackState.PlayingState else None)
            self.media.mediaStatusChanged.connect(lambda state:self.status.emit('Đã phát xong. Bạn có thể phát lại hoặc đổi giọng.')
                if state==QMediaPlayer.MediaStatus.EndOfMedia else None)
        except ImportError:
            self.process=QtCore.QProcess(self)
            self.process.errorOccurred.connect(lambda error:self.status.emit('Không mở được trình phát. Bạn có thể mở file WAV.'))

    def play(self,path):
        self.stop();self.requested.emit(str(path))
        if self.media:
            self.media.setSource(QtCore.QUrl.fromLocalFile(str(path)));self.media.play()
        elif shutil.which('mpv'):
            self.process.start('mpv',['--no-video','--really-quiet',str(path)])
            self.status.emit('Đang mở trình phát âm thanh…')
        else:self.status.emit('WAV đã tạo được. Cài Qt Multimedia hoặc mpv để phát, hoặc bấm Mở file WAV.')

    def stop(self):
        if self.media:self.media.stop()
        if self.process and self.process.state()!=QtCore.QProcess.ProcessState.NotRunning:self.process.kill()


class PreviewDialog(W.QDialog):
    def __init__(self,parent,root):
        super().__init__(parent);self.root=Path(root);self.config=load_config(self.root/'config/runtime.json')
        self.setWindowTitle('Nghe thử giọng');self.resize(650,470);self.busy=False;self.generation=0;self.wav=None
        from server import voices
        items=voices(self.config)
        layout=W.QVBoxLayout(self);layout.setContentsMargins(25,24,25,24);layout.setSpacing(13)
        layout.addWidget(label('Kiểm tra và nghe thử','title'))
        layout.addWidget(label('Chọn giọng, nhập câu và nghe qua thiết bị âm thanh của máy.','muted',True))
        self.voice=W.QComboBox()
        for identity,item in items.items():self.voice.addItem(VOICE_LABELS.get(item['folder'],item['folder']),identity)
        index=self.voice.findData(self.config.default_voice)
        if index>=0:self.voice.setCurrentIndex(index)
        layout.addWidget(self.voice)
        self.text=W.QTextEdit('こんにちは。今日はいい天気ですね。');self.text.setMaximumHeight(120);layout.addWidget(self.text)
        self.output=label('Sẵn sàng.','muted',True);layout.addWidget(self.output)
        row=W.QHBoxLayout();self.play_button=button('Phát thử',self.speak,True);row.addWidget(self.play_button)
        row.addWidget(button('Dừng',self.stop))
        self.open_button=button('Mở file WAV',self.open_file);self.open_button.setEnabled(False);row.addWidget(self.open_button)
        row.addStretch();row.addWidget(button('Đóng',self.close));layout.addLayout(row)
        layout.addWidget(label('Tạo WAV thành công xác nhận engine hoạt động. Việc nghe được còn phụ thuộc thiết bị đầu ra.','muted',True))
        self.playback=Playback(self);self.playback.status.connect(self.output.setText)
        self.text.textChanged.connect(self.invalidate);self.voice.currentIndexChanged.connect(self.invalidate)
        self.play_button.setEnabled(bool(items))
        if not items:self.output.setText('Chưa có giọng sẵn sàng. Hãy khởi tạo bản cài và kiểm tra dữ liệu giọng.')

    def invalidate(self,*args):
        self.generation+=1;self.wav=None;self.playback.stop();self.open_button.setEnabled(False)
        self.play_button.setText('Phát thử')
        if not self.busy:self.output.setText('Đã đổi nội dung hoặc giọng. Bấm Phát thử để tạo âm thanh.')

    def stop(self):
        self.generation+=1;self.playback.stop();self.output.setText('Đã dừng phát. Kết quả tổng hợp đang chờ sẽ không tự phát.')

    def speak(self):
        if self.busy:return
        text=self.text.toPlainText().strip();voice=self.voice.currentData()
        if not text or not voice:self.output.setText('Chọn giọng và nhập câu để nghe thử.');return
        if self.wav:self.playback.play(self.wav);return
        self.busy=True;self.play_button.setEnabled(False);self.output.setText('Đang tạo âm thanh…')
        self.generation+=1;token=self.generation
        def generate(report,progress):
            use_api=False
            try:
                with urllib.request.urlopen(self.config.api_url+'/healthz',timeout=1) as response:
                    health=json.load(response);use_api=isinstance(health,dict) and health.get('ready') and health.get('instance_id')==self.config.instance_id
            except (OSError,ValueError):pass
            if use_api:
                request=urllib.request.Request(self.config.api_url+'/v1/speak',json.dumps({'text':text,'voice':voice}).encode(),
                                               {'Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=120) as response:data=response.read()
                with wave.open(io.BytesIO(data)) as audio:
                    if audio.getnchannels()!=1 or audio.getsampwidth()!=2 or not audio.getnframes():raise ValueError('WAV không hợp lệ')
                folder=self.config.cache_dir;folder.mkdir(parents=True,exist_ok=True)
                output=folder/('demo_'+hashlib.sha256(data).hexdigest()+'.wav');output.write_bytes(data);return output
            from server import Engine
            engine=Engine(self.config)
            try:output,_,_=engine.speak(text,voice);return output
            finally:engine.stop()
        self.task=Task(generate)
        def done(path):
            self.busy=False;self.play_button.setEnabled(True)
            if token!=self.generation:self.output.setText('Đã bỏ kết quả cũ. Bấm Phát thử để nghe nội dung hiện tại.');return
            self.wav=Path(path);self.open_button.setEnabled(True)
            self.play_button.setText('Phát lại')
            self.output.setText('Tạo âm thanh thành công. Đang mở đầu ra âm thanh…');self.playback.play(path)
        def fail(message):
            self.busy=False;self.play_button.setEnabled(True);self.output.setText('Chưa tạo được âm thanh: '+message)
        self.task.succeeded.connect(done,Qt.ConnectionType.QueuedConnection)
        self.task.failed.connect(fail,Qt.ConnectionType.QueuedConnection);self.task.start()

    def open_file(self):
        if self.wav:QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.wav)))

    def closeEvent(self,event):self.stop();event.accept()


class ManagerWindow(W.QMainWindow):
    task_finished=Signal(bool)
    def __init__(self,payload,baseline,managed_root=None):
        super().__init__();self.payload=Path(payload);self.baseline=Path(baseline)
        self.busy=False;self.cancelled=threading.Event();self.install_complete=False;self.demo_dialog=None
        self.picker=Picker(self);self.setWindowTitle('A.I.VOICE2 + Anki');self.resize(1120,880);self.setMinimumSize(850,650)
        registry=self.payload/'runtime/voice_registry.json'
        if not registry.is_file():registry=RUNTIME/'voice_registry.json'
        self.registry=load_voice_registry(registry)
        central=W.QWidget();self.setCentralWidget(central)
        outer=W.QHBoxLayout(central);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        sidebar=W.QFrame();sidebar.setObjectName('sidebar');sidebar.setFixedWidth(195)
        nav=W.QVBoxLayout(sidebar);nav.setContentsMargins(18,28,18,20);nav.setSpacing(6)
        nav.addWidget(label('A.I.VOICE2','brand'));nav.addWidget(label('LOCAL VOICE · ANKI'));nav.addSpacing(28)
        self.nav=W.QButtonGroup(self);self.nav.setExclusive(True)
        for index,title in enumerate(['Cài đặt mới','Quản lý giọng','Nghe thử','Hỗ trợ']):
            item=button(title);item.setCheckable(True);self.nav.addButton(item,index);nav.addWidget(item)
        nav.addStretch();nav.addWidget(label('Một thư viện giọng.\nEditor và Anki cùng dùng.','muted',True))
        outer.addWidget(sidebar)
        right=W.QWidget();body=W.QVBoxLayout(right);body.setContentsMargins(0,0,0,0);body.setSpacing(0);outer.addWidget(right,1)
        top=W.QWidget();top_layout=W.QVBoxLayout(top);top_layout.setContentsMargins(26,22,26,12)
        heading=W.QHBoxLayout();heading.addWidget(label('GIỌNG NÓI CHO VIỆC HỌC TIẾNG NHẬT','eyebrow'),1)
        self.badge=label('Sẵn sàng','badge');heading.addWidget(self.badge);top_layout.addLayout(heading)
        self.title=label('Thiết lập không gian giọng nói','title');top_layout.addWidget(self.title)
        self.subtitle=label('Chọn ứng dụng và các giọng bạn muốn dùng trong Editor và Anki.','subtitle',True);top_layout.addWidget(self.subtitle)
        body.addWidget(top)
        self.pages=W.QStackedWidget();body.addWidget(self.pages,1)
        self.fields={};self.create_install();self.create_manage(managed_root);self.create_listen();self.create_support()
        self.create_footer(body)
        self.nav.idClicked.connect(self.navigate);self.nav.button(0).setChecked(True)
        self.scan_timer=QtCore.QTimer(self);self.scan_timer.setSingleShot(True);self.scan_timer.setInterval(200)
        self.scan_timer.timeout.connect(self.scan_install)
        self.fields['voicebanks'].changed.connect(lambda:self.scan_timer.start())
        self.fields['msi'].changed.connect(self.locate_adjacent)
        self.fields['destination'].changed.connect(self.reset_install_action)
        self.root_field.changed.connect(self.refresh_installed)
        if managed_root:self.navigate(1);self.nav.button(1).setChecked(True)
        self.refresh_installed()

    def page(self):
        area=W.QScrollArea();area.setWidgetResizable(True)
        content=W.QWidget();layout=W.QVBoxLayout(content);layout.setContentsMargins(26,6,26,22);layout.setSpacing(14)
        area.setWidget(content);self.pages.addWidget(area);return layout

    def create_install(self):
        page=self.page();frame,layout=card('1. Nguồn cài đặt','MSI và dữ liệu giọng được chọn riêng. Có thể dán đường dẫn vào các ô dưới.')
        grid=W.QGridLayout();grid.setHorizontalSpacing(16);grid.setVerticalSpacing(10)
        default=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'aivoice2-local'
        definitions=[('msi','Bộ cài A.I.VOICE2','MSI (*.msi)'),('voicebanks','Thư mục Voice / voicebanks',None),
                     ('languages','Thư mục Lang',None),('destination','Thư mục cài mới',None)]
        for index,(key,title,file_filter) in enumerate(definitions):
            field=PathField(title,self.picker,key,file_filter,value=str(default) if key=='destination' else '')
            self.fields[key]=field;grid.addWidget(field,index//2,index%2)
        layout.addLayout(grid);page.addWidget(frame)
        frame,layout=card('2. Chọn giọng','Akane tự dùng Kansai. Các giọng còn lại tự dùng Standard.')
        self.scan_summary=label('Chọn thư mục giọng để xem danh sách.','muted',True);layout.addWidget(self.scan_summary)
        self.install_voices=VoiceTable();layout.addWidget(self.install_voices);page.addWidget(frame)
        frame,layout=card('3. Kết nối ứng dụng')
        self.service_option=W.QCheckBox('Tạo shortcut và bật dịch vụ giọng nói khi đăng nhập');self.service_option.setChecked(True)
        self.anki_option=W.QCheckBox('Kết nối Anki đã cài trên máy');self.anki_option.setChecked(bool(shutil.which('anki')))
        layout.addWidget(self.service_option);layout.addWidget(self.anki_option)
        self.addons_field=PathField('Thư mục addon Anki',self.picker,'addons',value=str(Path.home()/'.local/share/Anki2/addons21'))
        layout.addWidget(self.addons_field);self.anki_option.toggled.connect(self.addons_field.setVisible)
        self.addons_field.setVisible(self.anki_option.isChecked());page.addWidget(frame)
        self.install_button=button('Cài đặt và kết nối',self.start_install,True)
        self.install_button.setObjectName('installButton');self.install_button.setProperty('primary',True)
        self.install_button.setEnabled((self.payload/'payload-manifest.json').is_file())
        page.addStretch()

    def create_manage(self,root):
        page=self.page();frame,layout=card('Bản cài đang quản lý')
        default=root or self.fields['destination'].text()
        self.root_field=PathField('Thư mục bản cài',self.picker,'managed-root',value=str(default));layout.addWidget(self.root_field)
        self.install_info=label('Chọn bản cài để xem giọng và thao tác bảo trì.','muted',True);layout.addWidget(self.install_info);page.addWidget(frame)
        frame,layout=card('Thư viện giọng')
        row=W.QHBoxLayout();self.add_button=button('Thêm giọng…',self.add_voices,True);row.addWidget(self.add_button)
        self.restore_button=button('Khôi phục giọng…',self.restore_voice);row.addWidget(self.restore_button);row.addStretch()
        self.remove_button=button('Gỡ giọng đã chọn',self.remove_voice);self.remove_button.setObjectName('danger');row.addWidget(self.remove_button)
        layout.addLayout(row);self.managed_voices=VoiceTable(checkable=False);layout.addWidget(self.managed_voices);page.addWidget(frame)
        frame,layout=card('Dịch vụ và kiểm tra','Lưu, đóng Editor rồi dừng dịch vụ trước khi thêm hoặc gỡ giọng.')
        row=W.QHBoxLayout();row.addWidget(button('Dừng dịch vụ',lambda:self.service_action(False)))
        row.addWidget(button('Bật dịch vụ',lambda:self.service_action(True)))
        self.initialize_button=button('Tiếp tục khởi tạo',self.initialize);row.addWidget(self.initialize_button)
        row.addStretch();layout.addLayout(row)
        layout.addWidget(button('Kết nối lại Anki…',self.reconnect));page.addWidget(frame);page.addStretch()

    def create_listen(self):
        page=self.page();frame,layout=card('Nghe thử giọng đã cài','Chọn giọng và câu mẫu. Âm thanh được phát qua thiết bị mặc định của máy.')
        layout.addWidget(label('Bạn có thể kiểm tra phát âm ngay tại đây mà không cần mở Editor hoặc Anki.','muted',True))
        layout.addWidget(button('Kiểm tra và nghe thử…',self.open_preview,True));page.addWidget(frame)
        page.addWidget(label('Bản cài được chọn trong mục Quản lý giọng.','muted',True));page.addStretch()

    def create_support(self):
        page=self.page();frame,layout=card('Thông tin hỗ trợ','Kiểm tra dữ liệu của bản cài hoặc lưu báo cáo để gửi khi cần.')
        layout.addWidget(button('Kiểm tra file bản cài',self.verify_files))
        layout.addWidget(button('Lưu báo cáo hỗ trợ…',self.export_support))
        layout.addWidget(label('Báo cáo chỉ chứa metadata đã ẩn đường dẫn chính. File được lưu trên máy, không tự gửi đi.','muted',True))
        page.addWidget(frame);page.addStretch()

    def create_footer(self,body):
        footer=W.QFrame();footer.setObjectName('footer');layout=W.QVBoxLayout(footer);layout.setContentsMargins(26,12,26,16);layout.setSpacing(9)
        row=W.QHBoxLayout();self.status=label('Sẵn sàng.','muted',True);row.addWidget(self.status,1)
        self.percent=label('0%','muted');row.addWidget(self.percent);layout.addLayout(row)
        self.progress=W.QProgressBar();self.progress.setRange(0,100);self.progress.setValue(0);self.progress.setTextVisible(False);self.progress.setObjectName('taskProgress');layout.addWidget(self.progress)
        row=W.QHBoxLayout();self.open_anki_button=button('Mở Anki',self.open_anki);row.addWidget(self.open_anki_button)
        self.open_editor_button=button('Mở A.I.VOICE2',self.open_editor);row.addWidget(self.open_editor_button)
        self.preview_button=button('Nghe thử…',self.open_preview);row.addWidget(self.preview_button)
        row.addStretch();self.cancel_button=button('Hủy sau bước hiện tại',self.cancelled.set);self.cancel_button.setVisible(False);row.addWidget(self.cancel_button)
        row.addWidget(self.install_button)
        self.details=W.QToolButton();self.details.setText('Chi tiết');self.details.setCheckable(True);row.addWidget(self.details)
        layout.addLayout(row);self.logs=W.QPlainTextEdit();self.logs.setReadOnly(True);self.logs.setMaximumHeight(100);self.logs.hide()
        self.details.toggled.connect(self.logs.setVisible);layout.addWidget(self.logs);body.addWidget(footer)

    def navigate(self,index):
        self.pages.setCurrentIndex(index)
        self.install_button.setVisible(index==0)
        titles=[('Thiết lập không gian giọng nói','Chọn ứng dụng và các giọng bạn muốn dùng trong Editor và Anki.'),
                ('Quản lý giọng và bản cài','Thêm, gỡ hoặc khôi phục giọng trong một thư viện dùng chung.'),
                ('Nghe trước khi bắt đầu','Chọn giọng, thử một câu và kiểm tra âm thanh trên máy.'),
                ('Hỗ trợ và kiểm tra','Thông tin cần thiết để tự kiểm tra hoặc nhờ hỗ trợ.')]
        self.title.setText(titles[index][0]);self.subtitle.setText(titles[index][1])

    def locate_adjacent(self,*args):
        source=Path(self.fields['msi'].text()).parent
        if (source/'Lang').is_dir() and not self.fields['languages'].text():self.fields['languages'].setText(source/'Lang')
        for name in ['voicebanks','Voice']:
            if (source/name).is_dir() and not self.fields['voicebanks'].text():self.fields['voicebanks'].setText(source/name)

    def scan_install(self):
        self.scan_timer.stop()
        if self.busy:return
        value=self.fields['voicebanks'].text()
        if not value:self.install_voices.populate([]);return
        source=normalize_source(value)
        try:items=scan_voicebanks(source,self.registry)
        except OSError as error:self.scan_summary.setText(str(error));return
        if (source.parent/'Lang').is_dir() and not self.fields['languages'].text():self.fields['languages'].setText(source.parent/'Lang')
        self.install_voices.populate(items)
        self.scan_summary.setText(f'Tìm thấy {len(items)} giọng trong {source.name}/. Chỉ các giọng được đánh dấu sẽ được cài.')

    def managed_root(self):return Path(self.root_field.text()).expanduser()

    def refresh_installed(self,*args):
        root=self.managed_root();valid=False
        try:
            data=json.loads((root/'install-manifest.json').read_text());config=load_config(root/'config/runtime.json')
            registry=load_voice_registry(config.voice_registry)
            items=[{'folder':name,'label':VOICE_LABELS.get(name,name),'language':registry.get(name,{}).get('language')}
                   for name in data['selected_voices']]
            self.managed_voices.populate(items,data['selected_voices']);self.install_info.setText(f'{len(items)} giọng · {root.name}')
            self.initialize_button.setVisible(data.get('status')!='native-checked');valid=True
        except (OSError,ValueError,KeyError):
            self.managed_voices.populate([]);self.install_info.setText('Chưa chọn được bản cài hợp lệ.');self.initialize_button.setVisible(False)
        for widget in [self.add_button,self.remove_button,self.restore_button,self.open_editor_button,self.preview_button]:widget.setEnabled(valid and not self.busy)
        self.open_anki_button.setEnabled(not self.busy)

    def set_progress(self,value,message):
        value=max(self.progress.value(),min(99,value)) if self.busy else value
        self.progress.setValue(value);self.percent.setText(str(value)+'%');self.status.setText(message)

    def begin_task(self,function,on_success=None,title='Đang xử lý…',cancelable=False):
        if self.busy:return
        if self.demo_dialog and self.demo_dialog.busy:
            W.QMessageBox.information(self,'Đang tạo âm thanh','Đợi câu nghe thử tạo xong trước khi thay đổi bản cài.');return
        self.busy=True;self.cancelled.clear();self.badge.setText('Đang xử lý');self.pages.setEnabled(False)
        self.install_button.setEnabled(False)
        self.progress.setValue(0);self.percent.setText('0%');self.status.setText(title);self.logs.clear()
        self.cancel_button.setVisible(cancelable)
        for widget in [self.open_anki_button,self.open_editor_button,self.preview_button]:widget.setEnabled(False)
        self.task=Task(function);self.task.reported.connect(self.report,Qt.ConnectionType.QueuedConnection)
        self.task.progressed.connect(self.set_progress,Qt.ConnectionType.QueuedConnection)
        def done(result):
            self.busy=False;self.pages.setEnabled(True);self.cancel_button.hide()
            self.install_button.setEnabled((self.payload/'payload-manifest.json').is_file())
            self.progress.setValue(100);self.percent.setText('100%');self.badge.setText('Hoàn tất');self.status.setText('Hoàn tất thao tác.')
            if on_success:on_success(result)
            self.refresh_installed();self.task_finished.emit(True)
        def fail(message):
            self.busy=False;self.pages.setEnabled(True);self.cancel_button.hide();self.badge.setText('Cần kiểm tra')
            self.install_button.setEnabled((self.payload/'payload-manifest.json').is_file())
            self.status.setText(message);self.logs.appendPlainText(message);self.refresh_installed();self.task_finished.emit(False)
            W.QMessageBox.warning(self,'Chưa hoàn tất',message)
        self.task.succeeded.connect(done,Qt.ConnectionType.QueuedConnection);self.task.failed.connect(fail,Qt.ConnectionType.QueuedConnection);self.task.start()

    def report(self,message):self.status.setText(message);self.logs.appendPlainText(message)

    def start_install(self):
        if self.install_complete:
            self.navigate(1);self.nav.button(1).setChecked(True);return
        if self.scan_timer.isActive():
            self.scan_install();self.status.setText('Đã cập nhật danh sách. Chọn giọng rồi bấm Cài đặt và kết nối.');return
        parameters={key:field.text() for key,field in self.fields.items()}
        selected=self.install_voices.selected()
        if not all(parameters.values()) or not selected:
            W.QMessageBox.information(self,'Chọn nguồn và giọng','Chọn đủ MSI, thư mục dữ liệu, nơi cài và ít nhất một giọng.');return
        from integrations import anki_is_running
        if self.anki_option.isChecked() and anki_is_running():
            W.QMessageBox.information(self,'Đóng Anki trước','Lưu công việc và đóng Anki, rồi tiếp tục cài đặt.');return
        parameters['voicebanks']=normalize_source(parameters['voicebanks'])
        service=self.service_option.isChecked();addons=self.addons_field.text() if self.anki_option.isChecked() else None
        def install(report,progress):
            config=install_files(**parameters,selected=selected,payload=self.payload,baseline=self.baseline,
                report=report,cancelled=self.cancelled.is_set,progress=lambda n,m:progress(int(n*.64),m))
            if self.cancelled.is_set():raise InterruptedError('Đã cài file. Có thể tiếp tục khởi tạo trong mục Quản lý giọng: '+str(config.parent.parent))
            initialize_runtime(config,report=report,progress=lambda n,m:progress(65+int(n*.27),m))
            progress(94,'Kết nối ứng dụng và tạo shortcut')
            if service or addons:
                from integrations import activate
                activate(config.parent.parent,addons,service,service,report)
            return config.parent.parent
        def installed(root):
            self.install_complete=True;self.root_field.setText(root)
            self.install_button.setText('Quản lý bản cài')
            self.status.setText('Cài đặt hoàn tất. Bạn có thể mở Anki, Editor hoặc nghe thử ngay bên dưới.')
        self.begin_task(install,installed,'Kiểm tra nguồn cài đặt…',True)

    def reset_install_action(self,*args):
        self.install_complete=False;self.install_button.setText('Cài đặt và kết nối')

    def add_voices(self):
        root=self.managed_root()
        try:
            data=json.loads((root/'install-manifest.json').read_text());config=load_config(root/'config/runtime.json')
            dialog=AddVoicesDialog(self,load_voice_registry(config.voice_registry),data['selected_voices'])
        except (OSError,ValueError) as error:W.QMessageBox.warning(self,'Chọn bản cài',str(error));return
        self.add_dialog=dialog
        if dialog.exec()!=W.QDialog.DialogCode.Accepted:return
        source=normalize_source(dialog.source.text());languages=dialog.languages.text();selected=dialog.voices.selected()
        def add(report,progress):
            from voice_manager import add_voices
            progress(5,'Kiểm tra giọng được chọn');add_voices(root,source,languages,selected,report)
        self.begin_task(add,title='Đang thêm giọng…')

    def remove_voice(self):
        selected=self.managed_voices.selected()
        if not selected:W.QMessageBox.information(self,'Chọn giọng','Chọn một dòng giọng trước khi gỡ.');return
        name=selected[0];root=self.managed_root()
        if W.QMessageBox.question(self,'Gỡ giọng',f'Chuyển {VOICE_LABELS.get(name,name)} vào bản dự phòng? Audio đã lưu trong Anki vẫn được giữ.')!=W.QMessageBox.StandardButton.Yes:return
        def remove(report,progress):
            from voice_manager import remove_voice
            return remove_voice(root,name,report)
        self.begin_task(remove,on_success=lambda token:self.status.setText('Đã gỡ giọng. Có thể khôi phục bằng nút Khôi phục giọng…'))

    def restore_voice(self):
        root=self.managed_root();choices={}
        for receipt in sorted((root/'backups/voices').glob('*/receipt.json'),reverse=True):
            try:
                data=json.loads(receipt.read_text())
                if data.get('state')=='removed':choices[VOICE_LABELS.get(data['voice'],data['voice'])+' · '+receipt.parent.name]=receipt.parent.name
            except (OSError,ValueError,KeyError):continue
        if not choices:W.QMessageBox.information(self,'Bản dự phòng','Chưa có giọng đã gỡ để khôi phục.');return
        choice,ok=W.QInputDialog.getItem(self,'Khôi phục giọng','Chọn bản giọng dự phòng',list(choices),0,False)
        if not ok:return
        def restore(report,progress):
            from voice_manager import restore_voice
            restore_voice(root,choices[choice],report)
        self.begin_task(restore)

    def service_action(self,start):
        root=self.managed_root()
        def run(report,progress):
            from integrations import start_owned_service,stop_owned_service
            (start_owned_service if start else stop_owned_service)(root)
        self.begin_task(run,on_success=lambda result:self.status.setText('Đã bật dịch vụ.' if start else 'Đã dừng dịch vụ của bản cài này.'))

    def initialize(self):
        root=self.managed_root()
        self.begin_task(lambda report,progress:initialize_runtime(root/'config/runtime.json',report,progress),
                        lambda result:self.status.setText('Đã khởi tạo. Bấm Nghe thử để phát âm thanh mẫu.'))

    def reconnect(self):
        root=self.managed_root();folder=self.picker.directory('Chọn thư mục addons21 của Anki','addons',self.addons_field.text())
        if not folder:return
        def run(report,progress):
            from integrations import activate
            activate(root,folder,True,True,report)
        self.begin_task(run)

    def open_preview(self):
        if self.busy:return
        if self.demo_dialog and (self.demo_dialog.isVisible() or self.demo_dialog.busy):
            self.demo_dialog.show();self.demo_dialog.raise_();self.demo_dialog.activateWindow();return
        try:self.demo_dialog=PreviewDialog(self,self.managed_root());self.demo_dialog.show()
        except (OSError,ValueError) as error:W.QMessageBox.warning(self,'Chưa nghe thử được',str(error))

    def open_editor(self):
        root=self.managed_root();runtime=root/'runtime/runtime_cli.py'
        if not runtime.is_file():return
        subprocess.Popen([sys.executable,str(runtime),'--config',str(root/'config/runtime.json'),'gui'])

    def open_anki(self):
        executable=shutil.which('anki') or self.picker.settings.value('anki/executable','')
        if not executable:
            executable=self.picker.file('Chọn chương trình Anki','anki-executable','Chương trình (*)')
            if not executable:return
            self.picker.settings.setValue('anki/executable',executable)
        try:subprocess.Popen([str(executable)])
        except OSError as error:W.QMessageBox.warning(self,'Chưa mở được Anki',str(error))

    def verify_files(self):
        root=self.managed_root()
        def verify(report,progress):
            from runtime_cli import verify_files
            result=verify_files(load_config(root/'config/runtime.json'))
            if not result['passed']:raise ValueError(json.dumps(result['failures'],ensure_ascii=False))
            return result['checked']
        self.begin_task(verify,lambda count:self.status.setText(f'Đã kiểm tra {count} file: khớp bản cài.'))

    def export_support(self):
        filename,_=W.QFileDialog.getSaveFileName(self,'Lưu báo cáo hỗ trợ',str(Path.home()/'aivoice2-support.zip'),'ZIP (*.zip)')
        if not filename:return
        root=self.managed_root()
        def export(report,progress):
            command=[sys.executable,str(root/'runtime/runtime_cli.py'),'--config',str(root/'config/runtime.json'),
                     '--output',filename,'export-support']
            result=subprocess.run(command,capture_output=True,text=True)
            if result.returncode:raise ValueError(result.stderr.strip())
        self.begin_task(export,lambda result:self.status.setText('Đã lưu báo cáo trên máy: '+filename))

    def closeEvent(self,event):
        if self.busy or self.demo_dialog and self.demo_dialog.busy:
            W.QMessageBox.information(self,'Đang xử lý','Đợi tác vụ hiện tại hoàn tất trước khi đóng.');event.ignore()
        else:
            if self.demo_dialog:self.demo_dialog.close()
            event.accept()


def run_app(payload,baseline,managed_root=None):
    app=W.QApplication.instance() or W.QApplication(sys.argv[:1])
    app.setStyle('Fusion');app.setStyleSheet(STYLE)
    window=ManagerWindow(payload,baseline,managed_root);window.show()
    return app.exec()
