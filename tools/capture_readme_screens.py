from pathlib import Path
import sys
from PIL import Image, ImageDraw
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'screenshots'
OUT.mkdir(parents=True, exist_ok=True)
DEMO = Path('/tmp/chouiui_readme_demo.gif')


def make_demo_gif():
    frames = []
    for i in range(8):
        frame = Image.new('RGBA', (352, 332), (34 + i * 8, 54, 78, 255))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((16 + i * 3, 18, 336 - i * 3, 314), outline=(224, 224, 224, 255), width=4)
        draw.rectangle((46, 78, 306, 252), fill=(16, 24, 34, 130), outline=(170, 190, 205, 255), width=2)
        draw.text((125, 154), f'FRAME {i + 1}', fill=(245, 245, 245, 255))
        frames.append(frame)
    frames[0].save(DEMO, save_all=True, append_images=frames[1:], duration=110, loop=0)


def pixmap(path):
    return QPixmap(str(path))


def capture_windows(app):
    import main
    window = main.App()
    window.show()
    window.load_gif_path(str(DEMO))

    def shot():
        window.grab().save(str(OUT / 'windows-app.png'))
        window.close()
        capture_android(app)

    QTimer.singleShot(650, shot)


def capture_android(app):
    root = QWidget()
    root.setFixedSize(420, 860)
    root.setStyleSheet('background:#111111; color:#e2e2e2;')
    layout = QVBoxLayout(root)
    layout.setContentsMargins(34, 28, 34, 28)
    layout.setSpacing(0)

    title = QLabel('ChouiUI')
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet('font-size:28px; font-weight:700; color:#e2e2e2;')
    subtitle = QLabel('GIF Converter')
    subtitle.setAlignment(Qt.AlignCenter)
    subtitle.setStyleSheet('font-size:14px; color:#989898;')
    layout.addWidget(title)
    layout.addWidget(subtitle)
    layout.addSpacing(28)

    preview = QLabel()
    preview.setFixedSize(352, 332)
    preview.setStyleSheet('background:#1b1b1b;')
    preview.setAlignment(Qt.AlignCenter)
    preview.setPixmap(pixmap(DEMO))
    layout.addWidget(preview, 0, Qt.AlignHCenter)
    info = QLabel('selected.gif  •  8 frames  •  352x332')
    info.setAlignment(Qt.AlignCenter)
    info.setStyleSheet('font-size:13px; color:#989898;')
    layout.addSpacing(16)
    layout.addWidget(info)
    layout.addSpacing(22)
    select = QPushButton('Select GIF')
    select.setFixedHeight(54)
    convert = QPushButton('Convert to .mcpack')
    convert.setFixedHeight(54)
    for button in (select, convert):
        button.setStyleSheet('QPushButton { background:#383838; color:#ffffff; border:0; border-radius:6px; font-size:14px; }')
    layout.addWidget(select)
    layout.addSpacing(10)
    layout.addWidget(convert)
    layout.addSpacing(18)
    folder = QLabel('Output folder                                      Change')
    folder.setStyleSheet('font-size:12px; color:#989898;')
    layout.addWidget(folder)
    folder_value = QLabel('Same folder as the GIF')
    folder_value.setStyleSheet('font-size:11px; color:#5a5a5a;')
    layout.addWidget(folder_value)
    status = QLabel('Ready to convert')
    status.setAlignment(Qt.AlignCenter)
    status.setStyleSheet('font-size:11px; color:#5a5a5a;')
    layout.addSpacing(20)
    layout.addWidget(status)
    root.show()

    def shot():
        root.grab().save(str(OUT / 'android-app-reference.png'))
        root.close()
        app.quit()

    QTimer.singleShot(200, shot)


if __name__ == '__main__':
    make_demo_gif()
    app = QApplication(sys.argv)
    capture_windows(app)
    app.exec()
    print('\n'.join(str(p) for p in sorted(OUT.glob('*.png'))))
