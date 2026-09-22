# ChouiUI GIF Converter

Convert any GIF into an animated `.mcpack` resource pack for Minecraft Bedrock using the ChouiUI v2.3 template.

## Current release features

- Matching clean dark interface on Windows and Android.
- Windows UI built with **PySide6** for a cleaner native-style layout.
- Frameless Windows window with the same dark color as the interface, no maximize button, and only minimize and close controls.
- One main action button: select a GIF, then convert it from the same button.
- A small gear icon opens a compact visual export-folder dialog.
- Animated preview: the preview loops through the same selected frames used for the pack and preserves the loop timing instead of playing too quickly or slowly.
- Animation speed is calculated from the original GIF duration.
- Up to 11 frames per pack to stay within Bedrock texture limits; longer GIFs are evenly resampled while preserving the overall loop duration.
- `pack_icon.png` is generated from the first frame of the selected GIF.
- The application icon is adapted from the supplied Minecraft inventory image in `assets/source_icon.jpg`.
- A new UUID is generated for every conversion.

## Image formats

The supplied source image is a **JPG image**. It is adapted to a balanced square icon without cutting off the important artwork, then converted into the Windows `.ico` and Android launcher PNG resources. When a GIF is converted, its first frame is separately written as the Minecraft pack's `pack_icon.png`.

## Windows

To run from source, install Python 3.8+ and the dependencies:

```bash
pip install -r requirements.txt
python main.py
```

The portable Windows executable is published in Releases as `ChouiGIFConverter.exe`.

## Android

The native Android project is located in `android/`. It uses the same visual layout, gear-folder dialog, dark colors and animated preview. To build it, use Android SDK, Gradle 8.10.2 and Java 17+:

```bash
cd android
./gradlew assembleRelease
```

The Android package is published in Releases as `ChouiGIFConverter.apk`.

## Usage

Select a GIF and press the main button. The preview animates using the same frame count and overall timing as the generated pack. Press the **gear icon** in the top-right corner to choose an output folder. If no custom folder is selected, Windows saves the `.mcpack` next to the GIF and Android opens the system save dialog.

The generated pack contains a horizontal frame strip, the Bedrock JSON `flip_book` animation, the inventory line overlay and a `pack_icon.png` generated from the first GIF frame.
