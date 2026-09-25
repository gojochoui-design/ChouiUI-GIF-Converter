from pathlib import Path
from PIL import Image, ImageDraw
import sys
import json
import zipfile

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
assert info.frame_count == 24
result = converter.convert(str(gif), str(out))
assert result.frame_count == 24
assert out.exists() and out.stat().st_size > 0
with zipfile.ZipFile(out) as pack:
    names = set(pack.namelist())
    assert 'textures/ui/inventory_flipbook_00.png' in names
    assert 'textures/ui/inventory_flipbook_01.png' in names
    common = json.loads(pack.read('ui/chouiui/chouiui_common.json'))
    assert common['inventory_flipbook_00']['frame_count'] == 23
    assert common['inventory_flipbook_01']['frame_count'] == 1
    assert common['segment_00_wait']['next'] == '@chouiui.segment_00_hide'
print(f'PASS: {result.original_count} original frames -> {result.frame_count} segmented flipbook frames')
