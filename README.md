# ChouiUI GIF Converter

A small tool that turns a GIF into an animated inventory resource pack for Minecraft Bedrock.

## What it changes

The pack changes the player's inventory in Survival and Creative. Other screens, such as crafting tables, furnaces, chests and anvils, keep the normal Minecraft interface.

Creative keeps the vanilla block browser and has a small menu button for switching sections.

## Windows

Install the dependencies and run the app:

```bash
pip install -r requirements.txt
python main.py
```

You can select a GIF, preview it and export an `.mcpack` file. The Windows app also supports dragging a GIF into the window.

## Android

The Android project is in the `android/` folder:

```bash
cd android
./gradlew assembleRelease
```

The APK lets you choose a GIF, preview it and save the generated `.mcpack` to a folder or through Android's save dialog. The output uses the GIF's name, so `example.gif` becomes `example.mcpack`.

## Animation

GIFs are exported as one safe sprite sheet with Aseprite frame metadata. The game reads the frame rectangles and durations directly, so there is no stack of independent textures and no transition between overlapping controls.

## Preview

![Windows app preview](docs/screenshots/windows-app-aalya.png)

![Android preview](docs/media/android-preview-aalya.gif)
