from pathlib import Path
from PIL import Image, ImageDraw
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import converter

root = Path('/tmp/chouiui-unlimited-test')
root.mkdir(parents=True, exist_ok=True)
gif = root / 'twenty-four.gif'
out = root / 'twenty-four.mcpack'
frames = []
for i in range(24):
    image = Image.new('RGBA', (32, 32), (20 + i, 30, 40, 255))
    ImageDraw.Draw(image).text((6, 10), str(i), fill='white')
    frames.append(image)
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=60, loop=0)
info = converter.probe(str(gif))
assert info.original_count == 24
assert info.frame_count == 23
result = converter.convert(str(gif), str(out))
assert result.frame_count == 23
assert out.exists() and out.stat().st_size > 0
print(f'PASS: {result.original_count} original frames -> {result.frame_count} safe flipbook frames')
