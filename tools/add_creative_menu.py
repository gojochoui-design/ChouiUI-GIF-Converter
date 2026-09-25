from pathlib import Path
import json

root = Path(__file__).resolve().parents[1] / 'template' / 'ui'
common_path = root / 'chouiui' / 'chouiui_common.json'
common = json.loads(common_path.read_text())
common['creative_inventory_menu'] = {
    '$pressed_button_name': 'button.inventory_right',
    'size': [14, 14],
    'layer': 30,
    'anchor_from': 'top_left',
    'anchor_to': 'top_left',
    'offset': [2, 2],
    'controls': [
        {'default': {'type': 'image', 'texture': 'textures/ui/chouiui_hamburger', 'size': ['100%', '100%']}},
        {'hover': {'type': 'image', 'texture': 'textures/ui/chouiui_hamburger_hover', 'size': ['100%', '100%']}},
        {'pressed': {'type': 'image', 'texture': 'textures/ui/chouiui_hamburger_pressed', 'size': ['100%', '100%']}},
    ],
}
common_path.write_text(json.dumps(common, indent=2, ensure_ascii=False) + '\n')

for filename, namespace, content_key in [
    ('override_inventory.json', 'crafting', 'chouiui_inventory_content'),
    ('override_inventory_pocket.json', 'crafting_pocket', 'chouiui_pocket_inventory_content'),
]:
    path = root / 'chouiui' / filename
    data = json.loads(path.read_text())
    content = data[content_key]
    controls = content['controls']
    controls[:] = [item for item in controls if 'creative_inventory_menu@chouiui.creative_inventory_menu' not in item]
    controls.append({'creative_inventory_menu@chouiui.creative_inventory_menu': {
        'bindings': [{'binding_type': 'global', 'binding_name': '#is_creative_mode', 'binding_name_override': '#visible'}]
    }})
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print('Added Creative-only hamburger control mapped to button.inventory_right.')
