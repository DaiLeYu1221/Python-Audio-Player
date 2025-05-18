import sys
import os
import sounddevice as sd
import soundfile as sf
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QKeySequence, QShortcut, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QFileDialog, QProgressBar,
    QMessageBox, QStyle, QListWidget, QListWidgetItem, QTextEdit
)

class AudioPlayer(QWidget):
    positionChanged = pyqtSignal(float)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.current_file = None
        self.position = 0
        self.duration = 0
        self.data = None
        self.samplerate = None
        self.stream = None
        self.volume = 1.0  # 默认音量为 1.0（最大音量）

    def load_file(self, file_path):
        try:
            self.current_file = file_path
            self.data, self.samplerate = sf.read(file_path)
            self.duration = len(self.data) / self.samplerate
            return True
        except Exception as e:
            print(f"加载文件失败: {e}")
            return False

    def play(self):
        if self.data is not None and not self.is_playing:
            self.is_playing = True
            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=self.data.shape[1],
                callback=self._audio_callback,
                finished_callback=self._play_finished
            )
            self.stream.start()

    def pause(self):
        if self.is_playing:
            self.is_playing = False
            self.stream.stop()

    def stop(self):
        if self.is_playing:
            self.is_playing = False
            self.stream.stop()
            self.position = 0

    def set_position(self, position):
        if self.data is not None:
            self.position = int(position * self.samplerate)

    def set_volume(self, volume):
        self.volume = volume  # 设置音量值

    def _audio_callback(self, outdata, frames, time, status):
        if self.is_playing:
            chunk = self.data[self.position:self.position + frames]
            outdata[:] = chunk * self.volume  # 应用音量
            self.position += frames
            self.positionChanged.emit(self.position / self.samplerate)
            if self.position >= len(self.data):
                self.is_playing = False

    def _play_finished(self):
        self.is_playing = False
        self.position = 0
        self.finished.emit()

class AudioPlayerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.playlist = []
        self.current_index = 0
        self.lyrics = {}
        self.initUI()
        self.player = AudioPlayer()
        self.setup_connections()

        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_lyrics)

    def initUI(self):
        self.setWindowTitle("PyQt6 Audio Player")
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(100, 100, 1000, 600)
        self.setAcceptDrops(True)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)

        # 左侧播放列表
        self.playlist_widget = QListWidget()
        self.playlist_widget.setMinimumWidth(250)
        layout.addWidget(self.playlist_widget)

        # 右侧控制面板
        right_panel = QVBoxLayout()
        layout.addLayout(right_panel)

        # 控制栏
        control_bar = QHBoxLayout()
        
        self.btn_open = QPushButton("打开文件")
        self.btn_open.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        
        self.btn_play = QPushButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.btn_play.setFixedSize(40, 40)
        
        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.btn_stop.setFixedSize(40, 40)
        
        self.btn_prev = QPushButton("⏮")
        self.btn_prev.setFixedSize(40, 40)
        
        self.btn_next = QPushButton("⏭")
        self.btn_next.setFixedSize(40, 40)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)

        control_bar.addWidget(self.btn_open)
        control_bar.addWidget(self.btn_prev)
        control_bar.addWidget(self.btn_play)
        control_bar.addWidget(self.btn_stop)
        control_bar.addWidget(self.btn_next)
        control_bar.addStretch()
        control_bar.addWidget(QLabel("音量:"))
        control_bar.addWidget(self.volume_slider)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        
        # 时间显示
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 歌词显示
        self.lyrics_text = QTextEdit()
        self.lyrics_text.setReadOnly(True)

        # 添加到布局
        right_panel.addLayout(control_bar)
        right_panel.addWidget(self.progress)
        right_panel.addWidget(self.time_label)
        right_panel.addWidget(self.lyrics_text)

        # 设置样式
        self._set_stylesheet()

    def _set_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E2E2E;
            }
            QListWidget {
                background-color: #404040;
                color: white;
                border: none;
            }
            QTextEdit {
                background-color: #404040;
                color: white;
                border: none;
            }
            QPushButton {
                background-color: #4A4A4A;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #404040;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -4px 0;
                background: #FFFFFF;
                border-radius: 8px;
            }
            QProgressBar {
                background-color: #404040;
                color: white;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078D7;
                border-radius: 4px;
            }
        """)

    def setup_connections(self):
        self.btn_open.clicked.connect(self.open_file)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_next.clicked.connect(self.next_track)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected)
        self.player.positionChanged.connect(self.update_progress)
        self.player.finished.connect(self.next_track)

        # 快捷键
        QShortcut(QKeySequence("Space"), self).activated.connect(self.toggle_play)
        QShortcut(QKeySequence("Q"), self).activated.connect(self.stop)
        QShortcut(QKeySequence("Left"), self).activated.connect(self.prev_track)
        QShortcut(QKeySequence("Right"), self).activated.connect(self.next_track)

    def open_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音频文件", "", "音频文件 (*.mp3 *.wav *.ogg)"
        )
        if files:
            for file in files:
                self.add_to_playlist(file)

    def add_to_playlist(self, path):
        if path not in self.playlist:
            self.playlist.append(path)
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.playlist_widget.addItem(item)

    def play_selected(self):
        try:
            selected = self.playlist_widget.currentRow()
            if selected >= 0:
                self.current_index = selected
                self.load_file(self.playlist[self.current_index])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"播放失败: {str(e)}")

    def prev_track(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_file(self.playlist[self.current_index])

    def next_track(self):
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.load_file(self.playlist[self.current_index])

    def load_file(self, path):
        try:
            if self.player.load_file(path):
                self.progress.setMaximum(int(self.player.duration))
                self.load_lyrics(path)
                self.player.play()
            else:
                QMessageBox.warning(self, "错误", "无法加载音频文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载音频文件失败: {str(e)}")

    def load_lyrics(self, path):
        try:
            lyrics_path = os.path.splitext(path)[0] + ".lrc"
            self.lyrics = {}
            if os.path.exists(lyrics_path):
                with open(lyrics_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "]" in line:
                            time_tag = line.split("]")[0][1:]
                            text = line.split("]")[1].strip()
                            self.lyrics[time_tag] = text
            self.lyrics_text.clear()
            self.lyrics_text.setPlainText("歌词加载完成" if self.lyrics else "未找到歌词文件")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载歌词失败: {str(e)}")

    def update_progress(self, current_time):
        self.progress.setValue(int(current_time))
        self.time_label.setText(
            f"{self.format_time(current_time)} / {self.format_time(self.player.duration)}"
        )

    def update_lyrics(self):
        current_time = self.player.position / self.player.samplerate
        time_str = self.format_time(current_time)
        if time_str in self.lyrics:
            self.lyrics_text.setPlainText(self.lyrics[time_str])

    def format_time(self, seconds):
        return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

    def toggle_play(self):
        if not self.player.current_file:
            QMessageBox.warning(self, "提示", "请先选择音频文件")
            return
            
        if self.player.is_playing:
            self.player.pause()
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            try:
                self.player.play()
                self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"播放失败: {str(e)}")

    def stop(self):
        """停止播放"""
        self.player.stop()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.statusBar().showMessage("播放已停止")

    def set_volume(self, volume):
        """设置音量"""
        try:
            print(f"当前音量值: {volume}")
            volume_normalized = volume / 100  # 将音量值从 0-100 映射到 0-1
            self.player.set_volume(volume_normalized)
            self.statusBar().showMessage(f"音量设置为: {volume}%")
        except Exception as e:
            print(f"设置音量失败: {e}")
            QMessageBox.critical(self, "错误", f"设置音量失败: {str(e)}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.add_to_playlist(file_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioPlayerGUI()
    window.show()
    sys.exit(app.exec())
