# ChouiUI GIF Converter 1.0

Convert any GIF into an animated `.mcpack` resource pack for Minecraft Bedrock using the ChouiUI v2.3 template.

## Scope of the generated pack

This 1.0 release changes only the player's inventory screen. **Survival and Creative use the same animated Java-style inventory UI**; the Creative block browser and its full block list are intentionally not added. The pack does not override the crafting table, furnace, smoker, blast furnace, brewing stand, anvil, enchanting table, redstone or chest screens. The game's original UI remains active everywhere else.

Both desktop and pocket inventory definitions use the same `java_inventory_panel` in survival and Creative mode.

## Features

- Matching clean dark interface on Windows and Android.
- Windows UI built with PySide6 in a frameless window with no maximize control.
- One main action button and a compact gear dialog for choosing the `.mcpack` export folder.
- Animated GIF preview using the same selected frames and overall timing as the generated pack.
- Up to 11 frames per pack to stay within Bedrock texture limits; longer GIFs are evenly resampled while preserving the overall loop duration.
- `pack_icon.png` generated from the first frame of the selected GIF.
- Application icon adapted from the supplied Minecraft inventory image.
- A new UUID is generated for every conversion.

## Windows

Install Python 3.8+ and the dependencies:

```bash
pip install -r requirements.txt
python main.py
```

The portable Windows executable is published as `ChouiGIFConverter.exe`.

## Android

The native Android project is located in `android/` and uses the same visual layout, gear dialog, dark colors and animated preview.

```bash
cd android
./gradlew assembleRelease
```

The Android package is published as `ChouiGIFConverter.apk` with version name `1.0`.

## Usage

Select a GIF and press the main button. The preview animates at the same overall speed as the generated pack. Press the gear icon in the top-right corner to choose an output folder. If no custom folder is selected, Windows saves the `.mcpack` next to the GIF and Android opens the system save dialog.
