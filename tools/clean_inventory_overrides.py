from pathlib import Path
import json

root = Path(__file__).resolve().parents[1] / 'template' / 'ui' / 'chouiui'

# The pack owns only the player inventory. Crafting tables and all other
# workstation screens must fall through to Bedrock's vanilla UI.
path = root / 'override_inventory.json'
data = json.loads(path.read_text())
data.pop('chouiui_crafting_content', None)
for key in list(data):
    if key.startswith('crafting_screen'):
        data.pop(key)
controls = data['chouiui_inventory_content']['controls'][0]['content_stack_panel']['controls']
for item in controls:
    if 'creative_browser@crafting.recipe_book' in item:
        item['creative_browser@crafting.recipe_inventory_screen_content'] = item.pop('creative_browser@crafting.recipe_book')
        item['creative_browser@crafting.recipe_inventory_screen_content']['size'] = ['fill', '100%']
        break
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

path = root / 'override_inventory_pocket.json'
data = json.loads(path.read_text())
data.pop('chouiui_pocket_crafting_content', None)
for key in list(data):
    if key.startswith('crafting_screen_pocket'):
        data.pop(key)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

for filename, key in [('inventory_screen.json', 'crafting_screen'), ('inventory_screen_pocket.json', 'crafting_screen_pocket')]:
    path = root.parent / filename
    data = json.loads(path.read_text())
    data.pop(key, None)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

common = root / 'chouiui_common.json'
data = json.loads(common.read_text())
data.pop('java_crafting_panel', None)
common.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

print('Cleaned crafting overrides; Creative keeps the vanilla recipe/block inventory content.')
