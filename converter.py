import json
import os
import re
import shutil
import sys
import tempfile
import uuid
import zipfile
from PIL import Image

ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT, "template")
STRIP_REL = os.path.join("textures", "ui", "inventory_flipbook.png")
LINES_REL = os.path.join("textures", "ui", "inventory_lines.png")
COMMON_REL = os.path.join("ui", "chouiui", "chouiui_common.json")
MAX_FRAMES = 11
FRAME_W, FRAME_H = 352, 332
DEFAULT_DELAY = 100
MIN_FPS, MAX_FPS = 2, 30

class GifInfo:
    def __init__(self, path, frame_count, fps, width, height, resampled, original_count=None):
        self.path, self.frame_count, self.fps = path, frame_count, fps
        self.width, self.height, self.resampled = width, height, resampled
        self.original_count = original_count if original_count is not None else frame_count

def read_frames(path):
    im = Image.open(path)
    im.load()
    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    frames, delays = [], []
    for idx in range(getattr(im, "n_frames", 1)):
        im.seek(idx)
        delays.append(im.info.get("duration", DEFAULT_DELAY) or DEFAULT_DELAY)
        canvas.alpha_composite(im.convert("RGBA"))
        frames.append(canvas.copy())
        if getattr(im, "disposal_method", 0) == 2:
            canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    return frames, delays

def resample_indices(total, target=MAX_FRAMES):
    if total <= target: return list(range(total))
    step = (total - 1) / float(target - 1)
    return list(dict.fromkeys(int(round(i * step)) for i in range(target)))

def fps_for_duration(delays, frame_count):
    total_ms = sum(d if d > 0 else DEFAULT_DELAY for d in delays)
    return max(MIN_FPS, min(MAX_FPS, int(round(frame_count * 1000.0 / max(total_ms, 1)))))

def probe(path):
    frames, delays = read_frames(path)
    selected = resample_indices(len(frames))
    return GifInfo(path, len(selected), fps_for_duration(delays, len(selected)), frames[0].width, frames[0].height, len(selected) < len(frames), len(frames))

def load_lines_overlay():
    return Image.open(os.path.join(TEMPLATE_DIR, LINES_REL)).convert("RGBA")

def compose_frame(frame, lines):
    base = frame.resize((FRAME_W, FRAME_H), Image.LANCZOS).convert("RGBA")
    base.alpha_composite(lines)
    return base

def build_strip(frames, progress=None):
    strip = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    lines = load_lines_overlay()
    for i, frame in enumerate(frames):
        strip.paste(compose_frame(frame, lines), (i * FRAME_W, 0))
        if progress: progress(i + 1, len(frames))
    return strip

def sanitize_pack_name(stem):
    name = re.sub(r"[^A-Za-z0-9 _-]", "", stem)
    return re.sub(r"\s+", " ", name).strip()[:48] or "Animated Inventory"

def patch_common(pack_dir, frame_count, fps):
    path = os.path.join(pack_dir, COMMON_REL)
    with open(path, encoding="utf-8") as f: data = json.load(f)
    data["inventory_flipbook"]["frame_count"] = frame_count
    data["inventory_flipbook"]["fps"] = fps
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def patch_manifest(pack_dir, frame_count, fps, gif_stem):
    path = os.path.join(pack_dir, "manifest.json")
    with open(path, encoding="utf-8") as f: data = json.load(f)
    name = sanitize_pack_name(gif_stem)
    data["header"].update(name=name, description=f"Animated inventory: {gif_stem} | {frame_count} frames @ {fps} fps", uuid=str(uuid.uuid4()), version=[1, 0, 0])
    data["modules"][0].update(uuid=str(uuid.uuid4()), version=[1, 0, 0])
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    return name

def convert(gif_path, out_path, progress=None, status=None):
    if not os.path.isfile(gif_path): raise FileNotFoundError(gif_path)
    with Image.open(gif_path) as im: im.verify()
    if status: status("Reading GIF...")
    frames, delays = read_frames(gif_path)
    if not frames: raise ValueError("No frames found in GIF")
    indices = resample_indices(len(frames))
    selected = [frames[i] for i in indices]
    fps = fps_for_duration(delays, len(selected))
    if status: status(f"Rendering {len(selected)} frames @ {fps} fps...")
    strip = build_strip(selected, progress)
    tmp = tempfile.mkdtemp(prefix="choui_gif_")
    try:
        pack_dir = os.path.join(tmp, "pack")
        shutil.copytree(TEMPLATE_DIR, pack_dir)
        strip.save(os.path.join(pack_dir, STRIP_REL), optimize=True)
        selected[0].convert("RGBA").resize((256, 256), Image.LANCZOS).save(os.path.join(pack_dir, "pack_icon.png"), optimize=True)
        patch_common(pack_dir, len(selected), fps)
        patch_manifest(pack_dir, len(selected), fps, os.path.splitext(os.path.basename(gif_path))[0])
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for root, _, files in os.walk(pack_dir):
                for name in files:
                    full = os.path.join(root, name)
                    z.write(full, os.path.relpath(full, pack_dir).replace(os.sep, "/"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if status: status("Done")
    return GifInfo(gif_path, len(selected), fps, frames[0].width, frames[0].height, len(selected) < len(frames), len(frames))

def default_output(gif_path, folder=None):
    name = sanitize_pack_name(os.path.splitext(os.path.basename(gif_path))[0]) + ".mcpack"
    return os.path.join(folder or os.path.dirname(os.path.abspath(gif_path)), name)

def preview_first_frame(gif_path):
    frames, _ = read_frames(gif_path)
    composed = compose_frame(frames[0], load_lines_overlay())
    bg = Image.new("RGBA", (FRAME_W, FRAME_H), (24, 24, 24, 255))
    bg.alpha_composite(composed)
    return bg.convert("RGB")

def preview_animation(gif_path):
    """Return every original GIF frame with its native delay.

    The generated Bedrock texture is safely resampled to 11 frames, but the
    desktop preview must remain smooth. Using every source frame here avoids
    the visibly slow 11-frame preview for long GIFs.
    """
    frames, delays = read_frames(gif_path)
    selected = [compose_frame(frame, load_lines_overlay()).convert("RGB") for frame in frames]
    return selected, [max(20, int(d if d > 0 else DEFAULT_DELAY)) for d in delays]
