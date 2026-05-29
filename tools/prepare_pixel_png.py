import argparse
import struct
import zlib
from pathlib import Path


TRANSPARENT = 0xF81F


def read_png_rgba(path):
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("Input file is not a PNG.")

    pos = 8
    width = height = color_type = bit_depth = None
    compressed = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        pos += 12 + length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filter, interlace = struct.unpack(">IIBBBBB", chunk_data)
            if bit_depth != 8 or color_type != 6 or interlace != 0:
                raise SystemExit("Only non-interlaced 8-bit RGBA PNG files are supported.")
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    raw = zlib.decompress(bytes(compressed))
    stride = width * 4
    rows = []
    prev = [0] * stride
    offset = 0
    for _y in range(height):
        filter_type = raw[offset]
        offset += 1
        row = list(raw[offset : offset + stride])
        offset += stride
        unfilter(row, prev, 4, filter_type)
        rows.append(row)
        prev = row
    return width, height, rows


def unfilter(row, prev, bpp, filter_type):
    if filter_type == 0:
        return
    if filter_type == 1:
        for i in range(len(row)):
            left = row[i - bpp] if i >= bpp else 0
            row[i] = (row[i] + left) & 0xFF
    elif filter_type == 2:
        for i in range(len(row)):
            row[i] = (row[i] + prev[i]) & 0xFF
    elif filter_type == 3:
        for i in range(len(row)):
            left = row[i - bpp] if i >= bpp else 0
            up = prev[i]
            row[i] = (row[i] + ((left + up) // 2)) & 0xFF
    elif filter_type == 4:
        for i in range(len(row)):
            left = row[i - bpp] if i >= bpp else 0
            up = prev[i]
            up_left = prev[i - bpp] if i >= bpp else 0
            row[i] = (row[i] + paeth(left, up, up_left)) & 0xFF
    else:
        raise SystemExit(f"Unsupported PNG filter: {filter_type}")


def paeth(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def pixel(rows, x, y):
    row = rows[y]
    i = x * 4
    return tuple(row[i : i + 4])


def same_color(a, b, tolerance):
    if a[3] == 0 and b[3] == 0:
        return True
    return sum(abs(a[i] - b[i]) for i in range(4)) <= tolerance


def detect_scale(width, height, rows, max_scale=8, tolerance=8):
    best_scale = 1
    best_score = 10**9
    for scale in range(2, max_scale + 1):
        blocks_x = width // scale
        blocks_y = height // scale
        if blocks_x == 0 or blocks_y == 0:
            continue
        mismatches = 0
        checked = 0
        for by in range(blocks_y):
            for bx in range(blocks_x):
                ref = pixel(rows, bx * scale, by * scale)
                for yy in range(scale):
                    for xx in range(scale):
                        checked += 1
                        if not same_color(ref, pixel(rows, bx * scale + xx, by * scale + yy), tolerance):
                            mismatches += 1
        score = mismatches * 1000000 // checked
        if score < best_score:
            best_score = score
            best_scale = scale
    return best_scale


def downsample(rows, width, height, scale):
    out_w = width // scale
    out_h = height // scale
    out = []
    for y in range(out_h):
        row = []
        for x in range(out_w):
            row.append(pixel(rows, x * scale, y * scale))
        out.append(row)
    return out_w, out_h, out


def trim_transparent(width, height, pixels):
    min_x = width
    min_y = height
    max_x = -1
    max_y = -1
    for y, row in enumerate(pixels):
        for x, color in enumerate(row):
            if color[3] != 0:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < 0:
        return width, height, pixels
    trimmed = [row[min_x : max_x + 1] for row in pixels[min_y : max_y + 1]]
    return max_x - min_x + 1, max_y - min_y + 1, trimmed


def crop_to(width, height, pixels, max_width, max_height):
    new_w = min(width, max_width)
    new_h = min(height, max_height)
    left = max(0, (width - new_w) // 2)
    top = max(0, (height - new_h) // 2)
    cropped = [row[left : left + new_w] for row in pixels[top : top + new_h]]
    return new_w, new_h, cropped


def write_png_rgba(path, width, height, pixels):
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b, a in row:
            raw.extend((r, g, b, a))
    chunks = [
        png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)),
        png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)),
        png_chunk(b"IEND", b""),
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + b"".join(chunks))


def png_chunk(chunk_type, data):
    body = chunk_type + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def write_rgb565_bin(path, pixels):
    out = bytearray()
    for row in pixels:
        for r, g, b, a in row:
            color = TRANSPARENT if a == 0 else rgb565(r, g, b)
            out.append((color >> 8) & 0xFF)
            out.append(color & 0xFF)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(out)


def main():
    parser = argparse.ArgumentParser(description="Shrink enlarged pixel-art PNG and export RGB565 data for Pico.")
    parser.add_argument("input")
    parser.add_argument("--png", default="assets/menu/background.png")
    parser.add_argument("--bin", default="assets/menu/background.bin")
    parser.add_argument("--scale", default="auto")
    parser.add_argument("--max-width", type=int, default=160)
    parser.add_argument("--max-height", type=int, default=120)
    parser.add_argument("--keep-border", action="store_true")
    args = parser.parse_args()

    width, height, rows = read_png_rgba(args.input)
    scale = detect_scale(width, height, rows) if args.scale == "auto" else int(args.scale)
    out_w, out_h, pixels = downsample(rows, width, height, scale)
    if not args.keep_border:
        out_w, out_h, pixels = trim_transparent(out_w, out_h, pixels)
    out_w, out_h, pixels = crop_to(out_w, out_h, pixels, args.max_width, args.max_height)

    write_png_rgba(args.png, out_w, out_h, pixels)
    write_rgb565_bin(args.bin, pixels)

    print(f"input: {width}x{height}")
    print(f"scale: {scale}")
    print(f"output: {out_w}x{out_h}")
    print(f"png: {args.png}")
    print(f"bin: {args.bin} ({out_w * out_h * 2} bytes)")


if __name__ == "__main__":
    main()
