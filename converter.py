import json
import os
import re
import shutil
import tempfile
import uuid
import zipfile

from PIL import Image, ImageSequence

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(ROOT, "template")
STRIP_REL = os.path.join("textures", "ui", "inventory_flipbook.png")
LINES_REL = os.path.join("textures", "ui", "inventory_lines.png")
COMMON_REL = os.path.join("ui", "chouiui", "chouiui_common.json")
MANIFEST_REL = "manifest.json"

PANEL_W = 176
PANEL_H = 166
FRAME_W = 352
FRAME_H = 332
MAX_FRAMES = 11
DEFAULT_DELAY = 100
MIN_FPS = 2
MAX_FPS = 30


class GifInfo:
    def __init__(self, path, frame_count, fps, width, height, resampled, original_count=None):
        self.path = path
        self.frame_count = frame_count
        self.fps = fps
        self.width = width
        self.height = height
        self.resampled = resampled
        self.original_count = original_count if original_count is not None else frame_count


def read_frames(path):
    im = Image.open(path)
    im.load()
    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    frames = []
    delays = []
    n = getattr(im, "n_frames", 1)
    for idx in range(n):
        im.seek(idx)
        delays.append(im.info.get("duration", DEFAULT_DELAY) or DEFAULT_DELAY)
        frame = im.convert("RGBA")
        canvas.alpha_composite(frame)
        frames.append(canvas.copy())
        if getattr(im, "disposal_method", 0) == 2:
            canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    return frames, delays


def average_fps(delays):
    clean = [d for d in delays if d > 0]
    if not clean:
        return 10
    avg = sum(clean) / len(clean)
    fps = int(round(1000.0 / avg)) if avg > 0 else 10
    return max(MIN_FPS, min(MAX_FPS, fps))


def resample_indices(total, target):
    if total <= target:
        return list(range(total))
    if target == 1:
        return [0]
    step = (total - 1) / float(target - 1)
    seen = set()
    out = []
    for i in range(target):
        v = int(round(i * step))
        if v in seen:
            v = min(total - 1, v + 1)
        while v in seen:
            v += 1
        seen.add(v)
        out.append(v)
    return out


def probe(path):
    frames, delays = read_frames(path)
    idx = resample_indices(len(frames), MAX_FRAMES)
    fps = average_fps(delays)
    return GifInfo(path, len(idx), fps, frames[0].width, frames[0].height, len(idx) < len(frames), len(frames))


def load_lines_overlay():
    return Image.open(os.path.join(TEMPLATE_DIR, LINES_REL)).convert("RGBA")


def compose_frame(gif_frame, lines):
    base = gif_frame.resize((FRAME_W, FRAME_H), Image.LANCZOS).convert("RGBA")
    base.alpha_composite(lines)
    return base


def build_strip(frames, progress=None):
    strip = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    lines = load_lines_overlay()
    for i, f in enumerate(frames):
        strip.paste(compose_frame(f, lines), (i * FRAME_W, 0))
        if progress:
            progress(i + 1, len(frames))
    return strip


def patch_common(pack_dir, frame_count, fps):
    path = os.path.join(pack_dir, COMMON_REL)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["inventory_flipbook"]["frame_count"] = frame_count
    data["inventory_flipbook"]["fps"] = fps
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sanitize_pack_name(stem):
    name = re.sub(r"[^A-Za-z0-9 _-]", "", stem)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:48] or "Animated Inventory"


def patch_manifest(pack_dir, frame_count, fps, gif_stem):
    path = os.path.join(pack_dir, MANIFEST_REL)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    name = sanitize_pack_name(gif_stem)
    data["header"]["name"] = name
    data["header"]["description"] = (
        "Animated inventory: %s | %d frames @ %d fps\n"
        "ChouiUI v2.3 Java 1.8.9 UI base" % (gif_stem, frame_count, fps))
    data["header"]["uuid"] = str(uuid.uuid4())
    data["header"]["version"] = [1, 0, 0]
    data["modules"][0]["uuid"] = str(uuid.uuid4())
    data["modules"][0]["version"] = [1, 0, 0]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return name


def write_mcpack(pack_dir, out_path):
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, _dirs, files in os.walk(pack_dir):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, pack_dir)
                z.write(full, rel.replace(os.sep, "/"))


def convert(gif_path, out_path, progress=None, status=None):
    if not os.path.isfile(gif_path):
        raise FileNotFoundError(gif_path)
    im = Image.open(gif_path)
    im.verify()
    if status:
        status("Reading GIF...")
    frames, delays = read_frames(gif_path)
    if not frames:
        raise ValueError("No frames found in GIF")
    fps = average_fps(delays)
    indices = resample_indices(len(frames), MAX_FRAMES)
    selected = [frames[i] for i in indices]
    resampled = len(selected) < len(frames)
    if status:
        status("Rendering %d frames @ %d fps..." % (len(selected), fps))
    strip = build_strip(selected, progress=progress)
    if status:
        status("Building pack...")
    tmp = tempfile.mkdtemp(prefix="choui_gif_")
    try:
        pack_dir = os.path.join(tmp, "pack")
        shutil.copytree(TEMPLATE_DIR, pack_dir)
        strip.save(os.path.join(pack_dir, STRIP_REL), optimize=True)
        patch_common(pack_dir, len(selected), fps)
        patch_manifest(pack_dir, len(selected), fps, os.path.splitext(os.path.basename(gif_path))[0])
        write_mcpack(pack_dir, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if status:
        status("Done: %s" % out_path)
    return GifInfo(gif_path, len(selected), fps, frames[0].width, frames[0].height, resampled, len(frames))


def default_output(gif_path):
    stem = os.path.splitext(os.path.basename(gif_path))[0]
    name = sanitize_pack_name(stem)
    return os.path.join(os.path.dirname(os.path.abspath(gif_path)), "%s.mcpack" % name)


def preview_first_frame(gif_path):
    frames, _delays = read_frames(gif_path)
    composed = compose_frame(frames[0], load_lines_overlay())
    bg = Image.new("RGBA", (FRAME_W, FRAME_H), (24, 24, 24, 255))
    bg.alpha_composite(composed)
    return bg.convert("RGB")
