from pathlib import Path
from PIL import Image, ImageDraw

out = Path(__file__).resolve().parents[1] / 'template' / 'textures' / 'ui' / 'chouiui_hamburger.png'
image = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((2, 2, 29, 26), radius=4, fill=(42, 42, 42, 255), outline=(210, 210, 210, 255), width=1)
draw.polygon([(8, 25), (8, 30), (14, 25)], fill=(42, 42, 42, 255))
for y in (9, 14, 19):
    draw.rectangle((8, y, 23, y + 1), fill=(245, 245, 245, 255))
image.save(out)
print(out)
