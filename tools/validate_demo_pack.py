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
    atlas = sorted(n for n in names if n.startswith('textures/ui/inventory_flipbook_') and n.endswith('.png'))
    assert len(atlas) == 7, atlas
    common = json.loads(pack.read('ui/chouiui/chouiui_common.json'))
    manifest = json.loads(pack.read('manifest.json'))
    assert manifest['header']['name'] == 'AalyaCorriendo'
    assert 'inventory_flipbook' not in common
    assert common['inventory_flipbook_00']['frame_count'] == 23
    assert common['inventory_flipbook_06']['frame_count'] == 13
    assert common['segment_06_wait']['next'] == '@chouiui.segment_06_hide'
    assert 'crafting_screen' not in pack.read('ui/inventory_screen.json').decode()
    assert 'crafting_screen_pocket' not in pack.read('ui/inventory_screen_pocket.json').decode()
print(f'PASS: {info.original_count} GIF frames -> {len(atlas)} atlas carriages, {info.fps} fps average')
