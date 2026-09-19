# ChouiUI GIF Converter
<img width="640" height="360" alt="este_00m08s-00m16s" src="https://github.com/user-attachments/assets/51cacb04-d4a7-4def-b129-ad32908be910" />

Turn any GIF into an animated player inventory background for Minecraft Bedrock, using the ChouiUI v2.3 template (Java Edition 1.8.9 UI port).

Built with Python. Modernized rework of the old MCPE-Inventory-Animator: the GIF is rendered at 2x resolution (352 x 332 per frame, the same HD size the old tool and Java animated GUI packs use), the texture animates through the native JSON UI `flip_book` animation (the technique vanilla itself uses for animated UI icons), and a black line overlay taken from the classic "inventario animado" Java pack is drawn on top so every slot stays readable.

## Crash-safe design

The pack is built to stay inside every known Bedrock limit that can hard-crash the game:

- **Horizontal frame strip** (`frame_step` in pixels, no `orientation` key), exactly mirroring the vanilla flipbook setups (walking icon, TNT icon, realms icons). Verified against vanilla: `test_anims_screen.json` uses 23 px steps for 23 px frames, `pdp_screen.json` uses 19 px steps.
- **Texture never exceeds 4096 px** on any side: max 11 frames at 352 x 332 = 3872 x 332 strip. Bigger strips (the old 40-frame / 13k px builds) can exceed the GPU texture limit and crash the game, especially on mobile.
- **Fresh UUIDs on every conversion** (header + module). The pack never collides with the ChouiUI v2.3 already installed, and converting the same GIF twice gives two independent packs.
- **Zip filename = manifest pack name** and the original ChouiUI `pack_icon.png` is kept untouched.
- Minimal vanilla-exact animation key set (`anim_type`, `initial_uv`, `frame_count`, `frame_step`, `fps`) plus `disable_anim_fast_forward`, like vanilla's own flipbook images.

## How it works

- Each GIF frame is resized to 352 x 332 (the 176 x 166 inventory panel at 2x, like Java HD GUI packs) and stacked into one horizontal strip PNG: `textures/ui/inventory_flipbook.png`.
- The template's inventory background (`java_bg_animated`) draws that strip with `"anim_type": "flip_book"` configured exactly like vanilla's own animated icons: `frame_step: 352`, plus `frame_count` and `fps` patched per GIF.
- No panel background is drawn anymore: the GIF is the background, so there is no gray fill anywhere.
- A static overlay (`textures/ui/inventory_lines.png`, extracted directly from the "Inventario Vacio" texture of the inventarioanimado Java pack) draws the black GUI outline, black slot borders and labels on top of the GIF at a higher layer, keeping the classic black-line look.
- The 3D player preview renders above the background (layer 8), so the player stays fully visible and can be rotated over the animation.
- Works on desktop and pocket UI (both use the same animated panel).
- Max 11 frames per pack (texture limit safe). Longer GIFs are evenly resampled to 11 frames so the full loop is kept.
- FPS is calculated from the GIF's own frame delays (clamped 2-30).

## Requirements

- Python 3.8+
- Pillow

```
pip install -r requirements.txt
```

## Usage

GUI:

```
run.bat        (Windows)
run.sh         (Linux / macOS)
python main.py
```

1. SELECT GIF
2. CONVERT
3. Import the generated `.mcpack` into Minecraft Bedrock.

CLI:

```
python main.py --cli my_animation.gif
```

## Output

`<gif name>.mcpack` next to the GIF by default. The zip filename always matches the pack name shown in Minecraft (taken from the GIF file name). Each conversion generates brand new pack UUIDs, so every pack is independent: you can keep several animated GIF packs installed at once.

## Notes

- Put this pack ABOVE the original ChouiUI in the active packs list (it already contains the full ChouiUI v2.3 files, so you can also use it alone).
- Only the survival inventory background is animated. Crafting table, furnace and other screens keep the original static ChouiUI textures.
- Transparent GIF areas show the world behind the panel instead of a fill, so transparent-background GIFs look great too.
- If the game crashed with an older build of this tool, delete the old converted pack from your packs before importing this one (the old builds reused the same pack UUID).

## Credits

- ChouiUI v2.3 template: ChouiUI author
- Black line overlay: "Inventario Vacio" texture from the inventarioanimado Java pack
- Original MCPE-Inventory-Animator concept: Swedeachu, CrisXolt, PolrFlare
- Animation technique: Minecraft Bedrock JSON UI `flip_book` (vanilla-proven)
