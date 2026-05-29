import argparse
import json
from pathlib import Path

from prepare_pixel_png import TRANSPARENT, read_png_rgba, rgb565, write_png_rgba


ROOT = Path(__file__).resolve().parents[1]
SPRITE_DIR = ROOT / "assets" / "sprites"
TILE_DIR = SPRITE_DIR / "tiles"


def parse_pair(text, value_type=int):
    left, right = text.split(",", 1)
    return value_type(left), value_type(right)


def parse_cell(text):
    if "=" in text:
        name, cell = text.split("=", 1)
    else:
        name = ""
        cell = text
    col, row = parse_pair(cell, int)
    return name, col, row


def pixel_at(rows, x, y):
    row = rows[y]
    i = x * 4
    return tuple(row[i : i + 4])


def crop(rows, x, y, size):
    return [[pixel_at(rows, x + col, y + row) for col in range(size)] for row in range(size)]


def to_rgb565_pixels(pixels):
    result = []
    for row in pixels:
        out_row = []
        for r, g, b, a in row:
            out_row.append(TRANSPARENT if a == 0 else rgb565(r, g, b))
        result.append(out_row)
    return result


def write_sprite(name, pixels, source):
    TILE_DIR.mkdir(parents=True, exist_ok=True)
    json_path = TILE_DIR / f"{name}.json"
    bin_path = TILE_DIR / f"{name}.bin"
    png_path = TILE_DIR / f"{name}.png"
    rgb565_pixels = to_rgb565_pixels(pixels)

    data = {
        "name": name,
        "type": "tile",
        "layer": "",
        "width": len(pixels[0]),
        "height": len(pixels),
        "transparent": TRANSPARENT,
        "format": "RGB565_BE",
        "source": source,
        "pixels": rgb565_pixels,
    }
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    raw = bytearray()
    for row in rgb565_pixels:
        for color in row:
            raw.append((color >> 8) & 0xFF)
            raw.append(color & 0xFF)
    bin_path.write_bytes(raw)
    write_png_rgba(png_path, len(pixels[0]), len(pixels), pixels)
    return json_path, bin_path, png_path


def sprite_json_files():
    if not SPRITE_DIR.exists():
        return []
    return [
        path
        for path in sorted(SPRITE_DIR.rglob("*.json"))
        if path.name != "manifest.json"
    ]


def update_manifest():
    sprites = []
    for path in sprite_json_files():
        data = json.loads(path.read_text(encoding="utf-8"))
        bin_path = path.with_suffix(".bin")
        sprites.append(
            {
                "name": data["name"],
                "type": data.get("type", "free"),
                "layer": data.get("layer", ""),
                "width": data["width"],
                "height": data["height"],
                "file": str(bin_path.relative_to(SPRITE_DIR)),
                "transparent": data.get("transparent", TRANSPARENT),
                "format": data.get("format", "RGB565_BE"),
            }
        )
    (SPRITE_DIR / "manifest.json").write_text(json.dumps({"sprites": sprites}, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Cut selected 8x8 tiles from a PNG sprite sheet.")
    parser.add_argument("image")
    parser.add_argument("cells", nargs="+", help="Cells as col,row or name=col,row. Example: dirt_2=3,4")
    parser.add_argument("--origin", default="0,0", help="Top-left corner of cell 0,0 in pixels.")
    parser.add_argument("--step", default="8,8", help="Distance between cell starts in pixels.")
    parser.add_argument("--tile", type=int, default=8, help="Tile size in pixels.")
    parser.add_argument("--prefix", default="", help="Prefix for unnamed output sprites.")
    args = parser.parse_args()

    origin_x, origin_y = parse_pair(args.origin, int)
    step_x, step_y = parse_pair(args.step, float)
    width, height, rows = read_png_rgba(args.image)

    written = []
    for index, cell_text in enumerate(args.cells, start=1):
        name, col, row = parse_cell(cell_text)
        if not name:
            name = f"{args.prefix}{index}" if args.prefix else f"tile_{col}_{row}"
        x = round(origin_x + col * step_x)
        y = round(origin_y + row * step_y)
        if x < 0 or y < 0 or x + args.tile > width or y + args.tile > height:
            raise SystemExit(f"Cell {col},{row} is outside image bounds at {x},{y}.")
        pixels = crop(rows, x, y, args.tile)
        written.append(write_sprite(name, pixels, f"{Path(args.image).name}:{col},{row}@{x},{y}"))

    update_manifest()
    for json_path, bin_path, png_path in written:
        print("wrote", json_path.relative_to(ROOT), bin_path.relative_to(ROOT), png_path.relative_to(ROOT))
    print("updated", (SPRITE_DIR / "manifest.json").relative_to(ROOT))


if __name__ == "__main__":
    main()
