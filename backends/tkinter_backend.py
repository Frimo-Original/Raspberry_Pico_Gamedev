import json
import time
import tkinter as tk
from pathlib import Path

from api import draw_text, sprite8_entries
from api.keys import Keys
from game_core.constants import SCALE, SCREEN_H, SCREEN_W


ROOT = Path(__file__).resolve().parents[1]
TRANSPARENT = 0xF81F
SWORD_FRAMES = 6


HIRES_PLAYER_ART = (
    "TTTTTHHHHHHTTTTT",
    "TTTTHHHHHHHHTTTT",
    "TTTHHHHHHHHHHTTT",
    "TTHHHHHHHHHHHHTT",
    "TTHHHSSSSSSHHHTT",
    "TTHHSSSSSSSSHHHT",
    "TTHHSESSSSESHHTT",
    "TTHHSSSSSSSSHTTT",
    "TTTHSSSMMSSHTTTT",
    "TTTTHSSSSSHTTTTT",
    "TTTTTSSSSSTTTTTT",
    "TTTRRRRRRRRRTTTT",
    "TTRRRRRRRRRRRTTT",
    "TTRRSSRRRRSSRTTT",
    "TTRRSSRRRRSSRTTT",
    "TTTRRRRRRRRTTTTT",
    "TTTTRRRRRRTTTTTT",
    "TTTTTPPPPTTTTTTT",
    "TTTTTPPPPTTTTTTT",
    "TTTTTPPPPTTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTBBTTTTBBTTTTT",
    "TTBBBBTTBBBBTTTT",
    "TTBBBBTTBBBBTTTT",
    "TTTBBTTTTBBTTTTT",
)

HIRES_PLAYER_COLORS = {
    "K": 0x0000,
    "S": 0xFDB8,
    "H": 0x4208,
    "E": 0x001F,
    "M": 0x6378,
    "R": 0x3D9F,
    "P": 0x18E3,
    "B": 0x0000,
}


def rgb565_to_hex(color):
    r = ((color >> 11) & 0x1F) * 255 // 31
    g = ((color >> 5) & 0x3F) * 255 // 63
    b = (color & 0x1F) * 255 // 31
    return "#%02x%02x%02x" % (r, g, b)


class TkRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.sprite8_pixels = self._load_sprite8_pixels()
        self.player_pixels = self._load_player_pixels()
        self.images = {}
        self._load_images()

    def clear(self, color):
        self.canvas.delete("all")
        self.rect(0, 0, SCREEN_W, SCREEN_H, color)

    def rect(self, x, y, w, h, color):
        self.canvas.create_rectangle(
            x * SCALE,
            y * SCALE,
            (x + w) * SCALE,
            (y + h) * SCALE,
            fill=rgb565_to_hex(color),
            outline="",
        )

    def tile(self, x, y, color, top_color):
        self.rect(x, y, 8, 8, color)
        self.rect(x, y, 8, 1, top_color)

    def tile_sprite(self, x, y, tile_id):
        self.sprite8(x, y, tile_id)

    def sprite8(self, x, y, sprite_id):
        pixels = self.sprite8_pixels.get(sprite_id)
        if pixels is None:
            return
        ox = x * SCALE
        oy = y * SCALE
        for row, line in enumerate(pixels):
            for col, color in enumerate(line):
                if color == TRANSPARENT:
                    continue
                self.canvas.create_rectangle(
                    ox + col * SCALE,
                    oy + row * SCALE,
                    ox + (col + 1) * SCALE,
                    oy + (row + 1) * SCALE,
                    fill=rgb565_to_hex(color),
                    outline="",
                )

    def text(self, x, y, text, color, scale=1):
        draw_text(self, x, y, text, color, scale)

    def player(self, x, y, flip_x=False):
        pixel = max(1, SCALE // 2)
        ox = x * SCALE - pixel
        oy = y * SCALE
        for row, line in enumerate(self.player_pixels):
            for col, color in enumerate(line):
                if color == TRANSPARENT:
                    continue
                draw_col = len(line) - 1 - col if flip_x else col
                self.canvas.create_rectangle(
                    ox + draw_col * pixel,
                    oy + row * pixel,
                    ox + (draw_col + 1) * pixel,
                    oy + (row + 1) * pixel,
                    fill=rgb565_to_hex(color),
                    outline="",
                )

    def image(self, x, y, name, w, h):
        image = self.images.get(name)
        if image is not None:
            self.canvas.create_image(x * SCALE, y * SCALE, image=image, anchor=tk.NW)

    def present(self):
        pass

    def _load_images(self):
        path = ROOT / "assets" / "menu" / "background.png"
        if path.exists():
            self.images["menu_background"] = tk.PhotoImage(file=str(path)).zoom(SCALE, SCALE)
        items_dir = ROOT / "assets" / "items"
        image_paths = [("copper_sword_icon", items_dir / "copper_sword_icon.png")]
        for side in ("r", "l"):
            for frame in range(SWORD_FRAMES):
                name = f"copper_sword_swing_{side}_{frame}"
                image_paths.append((name, items_dir / f"{name}.png"))
        for name, image_path in image_paths:
            if image_path.exists():
                self.images[name] = tk.PhotoImage(file=str(image_path)).zoom(SCALE, SCALE)

    def _load_player_pixels(self):
        path = ROOT / "assets" / "sprites" / "player_hires" / "player_default.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data["pixels"]
        return [[HIRES_PLAYER_COLORS.get(value, TRANSPARENT) for value in line] for line in HIRES_PLAYER_ART]

    def _load_sprite8_pixels(self):
        result = {}
        for sprite in sprite8_entries():
            path = ROOT / "assets" / "sprites" / sprite["file"].replace(".bin", ".json")
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                result[sprite["id"]] = data["pixels"]
        return result


class TkInput:
    def __init__(self, root, canvas):
        self.keys = Keys()
        self._pressed = set()
        root.bind("<KeyPress>", self._key_down)
        root.bind("<KeyRelease>", self._key_up)
        canvas.bind("<Motion>", self._mouse_move)
        canvas.bind("<ButtonPress-1>", self._dig_down)
        canvas.bind("<ButtonRelease-1>", self._dig_up)
        canvas.bind("<ButtonPress-2>", self._place_down)
        canvas.bind("<ButtonRelease-2>", self._place_up)
        canvas.bind("<ButtonPress-3>", self._place_down)
        canvas.bind("<ButtonRelease-3>", self._place_up)
        canvas.focus_set()

    def poll(self):
        self.keys.left = "Left" in self._pressed or "a" in self._pressed
        self.keys.right = "Right" in self._pressed or "d" in self._pressed
        self.keys.jump = "space" in self._pressed or "Up" in self._pressed or "w" in self._pressed
        return self.keys

    def _key_down(self, event):
        self._pressed.add(event.keysym)

    def _key_up(self, event):
        if event.keysym in self._pressed:
            self._pressed.remove(event.keysym)

    def _mouse_move(self, event):
        self.keys.cursor_x = event.x // SCALE
        self.keys.cursor_y = event.y // SCALE
        self.keys.cursor_active = True

    def _dig_down(self, event):
        self._mouse_move(event)
        self.keys.dig = True

    def _dig_up(self, event):
        self._mouse_move(event)
        self.keys.dig = False

    def _place_down(self, event):
        self._mouse_move(event)
        self.keys.place = True

    def _place_up(self, event):
        self._mouse_move(event)
        self.keys.place = False


def run(game):
    root = tk.Tk()
    root.title("Mini Terraria Portable")
    canvas = tk.Canvas(root, width=SCREEN_W * SCALE, height=SCREEN_H * SCALE, highlightthickness=0)
    canvas.pack()

    renderer = TkRenderer(canvas)
    controls = TkInput(root, canvas)
    frame_ms = 33

    def tick():
        start = time.time()
        game.update(controls.poll())
        game.draw(renderer)
        elapsed_ms = int((time.time() - start) * 1000)
        root.after(max(1, frame_ms - elapsed_ms), tick)

    tick()
    root.mainloop()
