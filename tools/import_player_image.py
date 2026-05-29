import argparse
import json
import re
import tkinter as tk
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPRITE_DIR = ROOT / "assets" / "sprites"
TRANSPARENT = 0xF81F


def sanitize_name(name):
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "player_default"


def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def load_png_pixels(path, width, height, transparent_top_left):
    root = tk.Tk()
    root.withdraw()
    image = tk.PhotoImage(file=str(path))
    source_w = image.width()
    source_h = image.height()

    transparent_rgb = image.get(0, 0) if transparent_top_left else None
    pixels = []

    for y in range(height):
        row = []
        sy = min(source_h - 1, int((y + 0.5) * source_h / height))
        for x in range(width):
            sx = min(source_w - 1, int((x + 0.5) * source_w / width))
            rgb = image.get(sx, sy)
            is_transparent = False
            try:
                is_transparent = bool(image.transparency_get(sx, sy))
            except tk.TclError:
                is_transparent = False
            if transparent_rgb is not None and rgb == transparent_rgb:
                is_transparent = True

            if is_transparent:
                row.append(TRANSPARENT)
            else:
                r, g, b = rgb
                color = rgb888_to_rgb565(r, g, b)
                if color == TRANSPARENT:
                    color = 0xF81E
                row.append(color)
        pixels.append(row)

    root.destroy()
    return pixels


def write_sprite(name, pixels, width, height):
    folder = SPRITE_DIR / "player_hires"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"{name}.json"
    bin_path = folder / f"{name}.bin"

    data = {
        "name": name,
        "type": "player_hires",
        "layer": "",
        "width": width,
        "height": height,
        "transparent": TRANSPARENT,
        "format": "RGB565_BE",
        "pixels": pixels,
    }
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    raw = bytearray()
    for row in pixels:
        for color in row:
            raw.append((color >> 8) & 0xFF)
            raw.append(color & 0xFF)
    bin_path.write_bytes(raw)
    update_manifest()
    return json_path, bin_path


def update_manifest():
    sprites = []
    for path in sorted(SPRITE_DIR.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if "pixels" not in data:
            continue
        bin_path = path.with_suffix(".bin")
        sprites.append({
            "name": data["name"],
            "type": data.get("type", "free"),
            "layer": data.get("layer", ""),
            "width": data["width"],
            "height": data["height"],
            "file": str(bin_path.relative_to(SPRITE_DIR)),
            "transparent": data.get("transparent", TRANSPARENT),
            "format": data.get("format", "RGB565_BE"),
        })
    (SPRITE_DIR / "manifest.json").write_text(json.dumps({"sprites": sprites}, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Import a PNG image as a 16x32 hi-res player sprite.")
    parser.add_argument("image", help="Path to PNG image.")
    parser.add_argument("--name", default="player_default", help="Sprite name. Default: player_default")
    parser.add_argument("--width", type=int, default=16, help="Output width. Default: 16")
    parser.add_argument("--height", type=int, default=32, help="Output height. Default: 32")
    parser.add_argument(
        "--transparent-top-left",
        action="store_true",
        help="Treat the source image top-left color as transparent.",
    )
    args = parser.parse_args()

    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    name = sanitize_name(args.name)
    pixels = load_png_pixels(image_path, args.width, args.height, args.transparent_top_left)
    json_path, bin_path = write_sprite(name, pixels, args.width, args.height)
    print(f"Saved {json_path.relative_to(ROOT)}")
    print(f"Saved {bin_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

