import argparse
import math
import subprocess
import tempfile
from pathlib import Path

from prepare_pixel_png import TRANSPARENT, read_png_rgba, rgb565, write_png_rgba


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "items"
SWING_ANGLES = (0, 25, 50, 75, 105, 135)


def load_rgba(path):
    path = Path(path)
    if path.suffix.lower() == ".png":
        return read_png_rgba(path)
    with tempfile.TemporaryDirectory() as temp_dir:
        png_path = Path(temp_dir) / "input.png"
        subprocess.run(["sips", "-s", "format", "png", str(path), "--out", str(png_path)], check=True)
        return read_png_rgba(png_path)


def pixel(rows, x, y):
    row = rows[y]
    i = x * 4
    return tuple(row[i : i + 4])


def resize_nearest(rows, width, height, out_w, out_h):
    result = []
    for y in range(out_h):
        src_y = min(height - 1, int((y + 0.5) * height / out_h))
        row = []
        for x in range(out_w):
            src_x = min(width - 1, int((x + 0.5) * width / out_w))
            row.append(pixel(rows, src_x, src_y))
        result.append(row)
    return result


def empty_rgba(w, h):
    return [[(0, 0, 0, 0) for _x in range(w)] for _y in range(h)]


def rotate_sprite(sprite, angle_degrees, out_size=32, pivot=(2, 14), offset=(8, 8)):
    angle = math.radians(angle_degrees)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    out = empty_rgba(out_size, out_size)
    for y, row in enumerate(sprite):
        for x, color in enumerate(row):
            if color[3] == 0:
                continue
            rel_x = x - pivot[0]
            rel_y = y - pivot[1]
            rx = rel_x * cos_a - rel_y * sin_a
            ry = rel_x * sin_a + rel_y * cos_a
            out_x = int(round(offset[0] + pivot[0] + rx))
            out_y = int(round(offset[1] + pivot[1] + ry))
            if 0 <= out_x < out_size and 0 <= out_y < out_size:
                out[out_y][out_x] = color
    return out


def flip_horizontal(sprite):
    return [list(reversed(row)) for row in sprite]


def rgba_to_rgb565_pixels(pixels):
    result = []
    for row in pixels:
        out_row = []
        for r, g, b, a in row:
            out_row.append(TRANSPARENT if a == 0 else rgb565(r, g, b))
        result.append(out_row)
    return result


def write_bin(path, pixels):
    raw = bytearray()
    for row in rgba_to_rgb565_pixels(pixels):
        for color in row:
            raw.append((color >> 8) & 0xFF)
            raw.append(color & 0xFF)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(raw)


def main():
    parser = argparse.ArgumentParser(description="Prepare Copper Shortsword assets for the game.")
    parser.add_argument("input")
    parser.add_argument("--name", default="copper_sword")
    args = parser.parse_args()

    width, height, rows = load_rgba(args.input)
    base = resize_nearest(rows, width, height, 16, 16)
    icon = resize_nearest(rows, width, height, 8, 8)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_png_rgba(OUT_DIR / f"{args.name}_icon.png", 8, 8, icon)
    write_bin(OUT_DIR / f"{args.name}_icon.bin", icon)
    write_png_rgba(OUT_DIR / f"{args.name}.png", 16, 16, base)
    write_bin(OUT_DIR / f"{args.name}.bin", base)

    for index, angle in enumerate(SWING_ANGLES):
        frame = rotate_sprite(base, angle)
        frame_left = flip_horizontal(frame)
        write_png_rgba(OUT_DIR / f"{args.name}_swing_r_{index}.png", 32, 32, frame)
        write_bin(OUT_DIR / f"{args.name}_swing_r_{index}.bin", frame)
        write_png_rgba(OUT_DIR / f"{args.name}_swing_l_{index}.png", 32, 32, frame_left)
        write_bin(OUT_DIR / f"{args.name}_swing_l_{index}.bin", frame_left)

    print(f"input: {width}x{height}")
    print(f"base: assets/items/{args.name}.png 16x16")
    print(f"icon: assets/items/{args.name}_icon.png 8x8")
    print(f"swing frames: {len(SWING_ANGLES)} right + {len(SWING_ANGLES)} left, 32x32")


if __name__ == "__main__":
    main()
