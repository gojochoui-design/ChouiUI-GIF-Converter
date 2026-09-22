import argparse
import json
import os
import sys
from pathlib import Path

from PIL.ImageQt import ImageQt
from PySide6.QtCore import QObject, QPoint, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QVBoxLayout, QWidget
)

import converter

BG = "#111111"
PANEL = "#1b1b1b"
BTN = "#2a2a2a"
HOVER = "#3b3b3b"
TEXT = "#e2e2e2"
DIM = "#989898"
ACCENT = "#7a7a7a"


def settings_path():
    return os.path.join(os.path.expanduser("~"), ".choui_gif_converter.json")


def load_settings():
    try:
        with open(settings_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"output_folder": ""}


def save_settings(data):
    with open(settings_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def pixmap_from_pil(image):
    return QPixmap.fromImage(ImageQt(image))


class FramelessWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos = QPoint()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < 58:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, parent, current):
        super().__init__(parent)
        self.setWindowTitle("Output folder")
        self.setModal(True)
        self.setFixedWidth(430)
        self.folder = current
        self.setStyleSheet(f"QDialog {{ background:{BG}; color:{TEXT}; }} QLabel {{ color:{DIM}; }} QLineEdit {{ background:{PANEL}; color:{TEXT}; border:1px solid #333; border-radius:7px; padding:8px; }} QPushButton {{ background:{BTN}; color:{TEXT}; border:0; border-radius:7px; padding:9px 14px; }} QPushButton:hover {{ background:{HOVER}; }}")
        box = QVBoxLayout(self)
        title = QLabel("EXPORT FOLDER")
        title.setStyleSheet(f"color:{TEXT}; font-size:13px; font-weight:700;")
        box.addWidget(title)
        box.addWidget(QLabel("Choose where converted .mcpack files will be saved."))
        row = QHBoxLayout()
        self.edit = QLineEdit(current or "Same folder as GIF")
        self.edit.setReadOnly(True)
        browse = QPushButton("Browse")
        browse.clicked.connect(self.browse)
        row.addWidget(self.edit, 1)
        row.addWidget(browse)
        box.addLayout(row)
        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet(f"background:{ACCENT}; color:white; border:0; border-radius:7px; padding:9px 18px;")
        apply_btn.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(apply_btn)
        box.addLayout(actions)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose export folder", self.folder or str(Path.home()))
        if folder:
            self.folder = folder
            self.edit.setText(folder)


class ConvertWorker(QObject):
    progress = Signal(int, int)
    status = Signal(str)
    done = Signal(object, str)
    failed = Signal(str)

    def __init__(self, gif_path, output):
        super().__init__()
        self.gif_path, self.output = gif_path, output

    def run(self):
        try:
            info = converter.convert(self.gif_path, self.output, progress=self.progress.emit, status=self.status.emit)
            self.done.emit(info, self.output)
        except Exception as exc:
            self.failed.emit(str(exc))


class App(FramelessWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.gif_path = None
        self.busy = False
        self.frames = []
        self.delays = []
        self.frame_index = 0
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.next_frame)
        self.thread = None
        self.worker = None
        self.setWindowTitle("ChouiUI GIF Converter")
        self.setFixedSize(560, 690)
        self.setStyleSheet(f"QWidget {{ background:{BG}; color:{TEXT}; }} QPushButton {{ background:{BTN}; color:{TEXT}; border:0; border-radius:7px; padding:10px 18px; font-weight:700; }} QPushButton:hover {{ background:{HOVER}; }} QPushButton:disabled {{ color:#5a5a5a; }} QProgressBar {{ background:{PANEL}; border:0; border-radius:4px; height:7px; }} QProgressBar::chunk {{ background:{ACCENT}; border-radius:4px; }}")
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 16, 22, 20)
        root.setSpacing(0)
        titlebar = QHBoxLayout()
        title = QLabel("CHOUIUI  •  GIF CONVERTER")
        title.setStyleSheet(f"font-size:16px; font-weight:700; color:{TEXT};")
        titlebar.addWidget(title)
        titlebar.addStretch()
        gear = QPushButton("⚙")
        gear.setToolTip("Export folder")
        gear.setFixedSize(38, 38)
        gear.setStyleSheet(f"QPushButton {{ background:transparent; color:{DIM}; font-size:21px; }} QPushButton:hover {{ color:{TEXT}; background:{PANEL}; }}")
        gear.clicked.connect(self.open_settings)
        minimize = QPushButton("—")
        minimize.setFixedSize(34, 34)
        minimize.clicked.connect(self.showMinimized)
        close = QPushButton("×")
        close.setFixedSize(34, 34)
        close.clicked.connect(self.close)
        titlebar.addWidget(gear)
        titlebar.addWidget(minimize)
        titlebar.addWidget(close)
        root.addLayout(titlebar)

        sub = QLabel("Animated inventory for Minecraft Bedrock")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color:{DIM}; font-size:9px;")
        root.addWidget(sub)
        self.select_btn = QPushButton("SELECT GIF")
        self.select_btn.setFixedHeight(44)
        self.select_btn.clicked.connect(self.select_gif)
        root.addSpacing(18)
        root.addWidget(self.select_btn, 0, Qt.AlignHCenter)
        self.info = QLabel("No GIF selected")
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setStyleSheet(f"color:{DIM}; font-size:9px;")
        root.addWidget(self.info)
        self.preview = QLabel()
        self.preview.setFixedSize(352, 332)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet(f"background:{PANEL};")
        root.addWidget(self.preview, 0, Qt.AlignHCenter)
        self.convert_btn = QPushButton("CONVERT GIF")
        self.convert_btn.setFixedHeight(46)
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self.convert_gif)
        root.addSpacing(10)
        root.addWidget(self.convert_btn, 0, Qt.AlignHCenter)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(360)
        self.progress.setVisible(False)
        root.addSpacing(6)
        root.addWidget(self.progress, 0, Qt.AlignHCenter)
        self.status = QLabel("Waiting for a GIF")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(f"color:{DIM}; font-size:8px;")
        root.addWidget(self.status)

    def open_settings(self):
        dialog = SettingsDialog(self, self.settings.get("output_folder", ""))
        if dialog.exec() == QDialog.Accepted:
            self.settings["output_folder"] = dialog.folder
            save_settings(self.settings)
            self.status.setText("Export folder updated")

    def select_gif(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select GIF", "", "GIF files (*.gif);;All files (*)")
        if not path:
            return
        self.gif_path = path
        self.info.setText(os.path.basename(path))
        self.status.setText("Reading GIF...")
        try:
            self.frames, self.delays = converter.preview_animation(path)
            info = converter.probe(path)
            self.info.setText(f"{os.path.basename(path)}  •  {info.original_count} frames  •  {info.width}x{info.height}")
            self.convert_btn.setEnabled(True)
            self.frame_index = 0
            self.show_frame()
            self.preview_timer.start(self.delays[0] if self.delays else 100)
            self.status.setText("Ready")
        except Exception:
            self.status.setText("Could not read this GIF")
            self.convert_btn.setEnabled(False)

    def show_frame(self):
        if self.frames:
            self.preview.setPixmap(pixmap_from_pil(self.frames[self.frame_index]))

    def next_frame(self):
        if not self.frames:
            return
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.show_frame()
        self.preview_timer.start(self.delays[self.frame_index] if self.delays else 100)

    def convert_gif(self):
        if not self.gif_path or self.busy:
            return
        self.busy = True
        self.select_btn.setEnabled(False)
        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        out = converter.default_output(self.gif_path, self.settings.get("output_folder") or None)
        self.thread = QThread(self)
        self.worker = ConvertWorker(self.gif_path, out)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(lambda done, total: self.progress.setMaximum(total) or self.progress.setValue(done))
        self.worker.status.connect(self.status.setText)
        self.worker.done.connect(self.conversion_done)
        self.worker.failed.connect(self.conversion_failed)
        self.worker.done.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def conversion_done(self, info, output):
        self.busy = False
        self.select_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.status.setText(f"Saved: {os.path.basename(output)}")
        self.info.setText(f"{os.path.basename(self.gif_path)}  •  {info.frame_count} frames @ {info.fps} fps")

    def conversion_failed(self, error):
        self.busy = False
        self.select_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.status.setText("Could not convert this GIF")


def run_cli(args):
    converter.convert(args.cli, args.output or converter.default_output(args.cli, args.folder))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli")
    parser.add_argument("-o", "--output")
    parser.add_argument("--folder")
    args = parser.parse_args()
    if args.cli:
        run_cli(args)
        return
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "assets", "choui_icon.ico")))
    window = App()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
