from pathlib import Path
import json
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import converter

root = Path(__file__).resolve().parents[1]
gif = Path('/home/ubuntu/upload/AalyaCorriendo.gif')
out = Path('/tmp/aalya-segmented.mcpack')
info = converter.convert(str(gif), str(out))
assert info.original_count == 151
assert info.frame_count == 151
with zipfile.ZipFile(out) as pack:
    names = set(pack.namelist())
    assert 'textures/ui/inventory_flipbook.png' in names
    assert 'textures/ui/inventory_flipbook.json' in names
    common = json.loads(pack.read('ui/chouiui/chouiui_common.json'))
    manifest = json.loads(pack.read('manifest.json'))
    assert manifest['header']['name'] == 'AalyaCorriendo'
    assert common['inventory_flipbook']['anim_type'] == 'aseprite_flip_book'
    aseprite = json.loads(pack.read('textures/ui/inventory_flipbook.json'))
    assert len(aseprite['frames']) == 151
    assert 'crafting_screen' not in pack.read('ui/inventory_screen.json').decode()
    assert 'crafting_screen_pocket' not in pack.read('ui/inventory_screen_pocket.json').decode()
print(f'PASS: {info.original_count} GIF frames -> one {aseprite["meta"]["size"]["w"]}x{aseprite["meta"]["size"]["h"]} Aseprite sheet, {info.fps} fps average')
