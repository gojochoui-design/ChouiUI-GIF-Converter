import json
import shutil
from pathlib import Path

root = Path('/home/ubuntu/repo_update')
for base in [root / 'template', root / 'android/app/src/main/assets/template']:
    ui = base / 'ui'
    # Keep only the UI definition files needed for the player's inventory.
    defs = {
        'ui_defs': [
            'ui/chouiui/chouiui_common.json',
            'ui/chouiui/override_inventory.json',
            'ui/chouiui/override_inventory_pocket.json',
            'ui/inventory_screen.json',
            'ui/inventory_screen_pocket.json',
        ]
    }
    (ui / '_ui_defs.json').write_text(json.dumps(defs, indent=2) + '\n', encoding='utf-8')
    for name in ('override_inventory.json', 'override_inventory_pocket.json'):
        path = ui / 'chouiui' / name
        data = json.loads(path.read_text(encoding='utf-8'))
        for key in list(data):
            if 'crafting' in key and key not in ('chouiui_inventory_content', 'chouiui_pocket_inventory_content'):
                del data[key]
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    desktop = ui / 'chouiui' / 'override_inventory.json'
    data = json.loads(desktop.read_text(encoding='utf-8'))
    content = data['chouiui_inventory_content']
    content['controls'][0]['content_stack_panel']['controls'] = [
        {'java_inventory@chouiui.java_inventory_panel': {'layer': 2}}
    ]
    desktop.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    pocket = ui / 'chouiui' / 'override_inventory_pocket.json'
    data = json.loads(pocket.read_text(encoding='utf-8'))
    content = data['chouiui_pocket_inventory_content']
    content['controls'] = [
        {'java_inventory@chouiui.java_inventory_panel': {}}
    ]
    pocket.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    inv = {
        'inventory_screen': {
            'variables': [
                {'requires': '$desktop_screen', '$screen_content': 'crafting.chouiui_inventory_content', '$screen_bg_content': 'common.screen_background', '$screen_background_alpha': 0.4},
                {'requires': '$pocket_screen', '$screen_content': 'crafting.chouiui_inventory_content', '$screen_bg_content': 'common.screen_background', '$screen_background_alpha': 0.4},
            ]
        }
    }
    (ui / 'inventory_screen.json').write_text(json.dumps(inv, indent=2) + '\n', encoding='utf-8')
    inv_pocket = {
        'inventory_screen_pocket': {
            'variables': [
                {'requires': '$desktop_screen', '$screen_content': 'crafting_pocket.chouiui_pocket_inventory_content', '$screen_bg_content': 'common.screen_background', '$screen_background_alpha': 0.4},
                {'requires': '$pocket_screen', '$screen_content': 'crafting_pocket.chouiui_pocket_inventory_content', '$screen_bg_content': 'common.screen_background', '$screen_background_alpha': 0.4},
            ]
        }
    }
    (ui / 'inventory_screen_pocket.json').write_text(json.dumps(inv_pocket, indent=2) + '\n', encoding='utf-8')
    for filename in ('chest_screen.json', 'furnace_screen.json', 'smoker_screen.json', 'blast_furnace_screen.json', 'brewing_stand_screen.json', 'anvil_screen.json', 'enchanting_screen.json', 'redstone_screen.json'):
        (ui / filename).unlink(missing_ok=True)
    (ui / 'chouiui' / 'chouiui_screens.json').unlink(missing_ok=True)
