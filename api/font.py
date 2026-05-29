FONT_3X5 = {
    " ": ("000", "000", "000", "000", "000"),
    "A": ("010", "101", "111", "101", "101"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "G": ("111", "100", "101", "101", "111"),
    "I": ("111", "010", "010", "010", "111"),
    "L": ("100", "100", "100", "100", "111"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "P": ("110", "101", "110", "100", "100"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
}


def text_width(text, scale=1):
    if not text:
        return 0
    return (len(text) * 4 - 1) * scale


def draw_text(gfx, x, y, text, color, scale=1):
    cursor_x = x
    for char in text.upper():
        pattern = FONT_3X5.get(char, FONT_3X5[" "])
        for row, line in enumerate(pattern):
            for col, pixel in enumerate(line):
                if pixel == "1":
                    gfx.rect(cursor_x + col * scale, y + row * scale, scale, scale, color)
        cursor_x += 4 * scale
