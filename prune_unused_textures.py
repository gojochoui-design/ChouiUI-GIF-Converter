from pathlib import Path
keep = {
    'brewing_fuel_slot.png',
    'chouiui_cell_selected.png',
    'chouiui_close_x.png',
    'chouiui_close_x_hover.png',
    'chouiui_close_x_pressed.png',
    'chouiui_transparent.png',
    'inventory.png',
    'inventory_flipbook.png',
    'inventory_lines.png',
}
for base in [Path('/home/ubuntu/repo_update/template'), Path('/home/ubuntu/repo_update/android/app/src/main/assets/template')]:
    folder = base / 'textures' / 'ui'
    for path in folder.glob('*.png'):
        if path.name not in keep:
            path.unlink()
