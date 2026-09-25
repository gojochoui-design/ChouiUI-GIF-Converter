from pathlib import Path
import os
import shutil
import sys
from PIL import Image
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'screenshots'
MEDIA = ROOT / 'docs' / 'media'
OUT.mkdir(parents=True, exist_ok=True)
MEDIA.mkdir(parents=True, exist_ok=True)
SOURCE = Path(os.environ.get('CHOUIUI_DEMO_GIF', '/home/ubuntu/upload/AalyaCorriendo.gif'))


def capture_windows(app):
    import main
    window = main.App()
    window.show()
    window.load_gif_path(str(SOURCE))

    def shot():
        window.grab().save(str(OUT / 'windows-app-aalya.png'))
        window.close()
        make_android_preview_gif(app)

    QTimer.singleShot(900, shot)


def make_android_preview_gif(app):
    import converter
    frames, delays = converter.preview_animation(str(SOURCE))
    pil_frames = []
    for frame in frames:
        image = frame.convert('RGB').resize((176, 166), Image.Resampling.LANCZOS)
        pil_frames.append(image)
    pil_frames[0].save(
        MEDIA / 'android-preview-aalya.gif',
        save_all=True,
        append_images=pil_frames[1:],
        duration=delays,
        loop=0,
        optimize=False,
    )
    shutil.copy2(SOURCE, MEDIA / 'AalyaCorriendo-original.gif')
    app.quit()


if __name__ == '__main__':
    if not SOURCE.exists():
        raise SystemExit(f'Missing real demo GIF: {SOURCE}')
    app = QApplication(sys.argv)
    capture_windows(app)
    app.exec()
    print(OUT / 'windows-app-aalya.png')
    print(MEDIA / 'android-preview-aalya.gif')
    print(MEDIA / 'AalyaCorriendo-original.gif')
