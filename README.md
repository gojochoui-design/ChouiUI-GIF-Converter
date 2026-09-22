# ChouiUI GIF Converter

Convert any GIF into an animated `.mcpack` resource pack for Minecraft Bedrock using the ChouiUI v2.3 template.

## Current release features

- Matching clean dark interface on Windows and Android.
- One main action button: select a GIF, then convert it from the same button.
- A small gear icon in the top-right corner opens the output-folder picker.
- No permanent settings panel or extra settings buttons.
- Animation speed is calculated from the original GIF duration.
- Up to 11 frames per pack to stay within Bedrock texture limits; longer GIFs are evenly resampled while preserving the overall loop duration.
- `pack_icon.png` is generated from the first frame of the selected GIF.
- The application icon is adapted from the supplied Minecraft inventory image in `assets/source_icon.jpg` and stored as `assets/choui_icon_adapted.png`.
- A new UUID is generated for every conversion.

## Image formats

The supplied source image is a **JPG image**. It is adapted to a balanced square icon without cutting off the important artwork, then converted into the Windows `.ico` and Android launcher PNG resources. When a GIF is converted, its first frame is separately written as the Minecraft pack's `pack_icon.png`.

## Windows

To run from source, install Python 3.8+ and Pillow:

```bash
pip install -r requirements.txt
python main.py
```

The portable Windows executable is published in Releases as `ChouiGIFConverter.exe`.

## Android

The native Android project is located in `android/`. To build it, use Android SDK, Gradle 8.10.2 and Java 17+:

```bash
cd android
./gradlew assembleRelease
```

The Android package is published in Releases as `ChouiGIFConverter.apk`.

## Usage

Select a GIF and press the main button. Press the **gear icon** in the top-right corner to choose an output folder. If no custom folder is selected, Windows saves the `.mcpack` next to the GIF and Android opens the system save dialog.

The generated pack contains a horizontal frame strip, the Bedrock JSON `flip_book` animation, the inventory line overlay and a `pack_icon.png` generated from the first GIF frame.

## Build outputs

The latest release includes:

- `ChouiGIFConverter.exe` — portable Windows 64-bit application.
- `ChouiGIFConverter.apk` — signed Android application.
- `ChouiGIFConverter-source.zip` — source code archive.
