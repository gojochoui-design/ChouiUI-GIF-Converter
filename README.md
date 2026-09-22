# ChouiUI GIF Converter

Convierte un GIF en un paquete `.mcpack` animado para Minecraft Bedrock usando la plantilla ChouiUI v2.3.

## Cambios de esta versión

- Interfaz Windows y Android sobria, oscura y sin colores chillones.
- Un único botón principal: selecciona el GIF y después se convierte en el mismo botón.
- Sección de ajustes para elegir la carpeta de salida del `.mcpack`.
- Se conserva la duración total del GIF al calcular la velocidad de reproducción.
- Hasta 11 frames por paquete para respetar el límite seguro de texturas de Bedrock; los GIF más largos se reducen uniformemente.
- `pack_icon.png` se genera con el primer frame del GIF convertido.
- El icono de la aplicación usa la imagen incluida en `assets/source_icon.jpg`.
- UUID nuevo en cada conversión.

## Windows

Requisitos para ejecutar desde fuente: Python 3.8+ y Pillow.

```bash
pip install -r requirements.txt
python main.py
```

El ejecutable portable se publica en Releases como `ChouiGIFConverter.exe`.

## Android

El proyecto Android nativo está en `android/`. Para compilarlo se necesita Android SDK, Gradle 8.10.2 y Java 17+.

```bash
cd android
./gradlew assembleRelease
```

El APK publicado aparece en Releases como `ChouiGIFConverter.apk`.

## Uso

Selecciona un GIF y pulsa el botón principal. En **Settings** puedes elegir una carpeta de salida. Si no se elige una carpeta, Windows guarda junto al GIF y Android muestra el selector de guardado del sistema.

El paquete generado contiene una tira horizontal de frames, la animación JSON `flip_book`, las líneas de inventario y un `pack_icon.png` tomado del primer frame del GIF.
