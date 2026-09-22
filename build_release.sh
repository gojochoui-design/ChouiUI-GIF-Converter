#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/release"
PYINSTALLER_PY="$(find "$HOME/.wine/drive_c" -type f -iname python.exe | head -1)"
if [ -n "$PYINSTALLER_PY" ]; then
  WINEPREFIX="$HOME/.wine" wine "$PYINSTALLER_PY" -m PyInstaller --noconfirm --clean --onefile --windowed --icon "Z:$ROOT/assets/choui_icon.ico" --add-data "Z:$ROOT/template;template" --add-data "Z:$ROOT/assets/choui_icon.ico;assets" --name ChouiGIFConverter "Z:$ROOT/main.py"
  cp "$HOME/dist/ChouiGIFConverter.exe" "$ROOT/release/ChouiGIFConverter.exe"
fi
if [ -n "${ANDROID_SDK_ROOT:-}" ] && [ -x "$ROOT/android/gradlew" ]; then
  (cd "$ROOT/android" && ./gradlew assembleRelease)
  cp "$ROOT/android/app/build/outputs/apk/release/app-release-unsigned.apk" "$ROOT/release/ChouiGIFConverter-unsigned.apk"
fi
