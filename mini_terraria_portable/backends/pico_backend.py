from api import draw_text, sprite8_entries
from api.keys import Keys

try:
    import sys
    import select
except ImportError:
    sys = None
    select = None

try:
    import game
except ImportError:
    game = None

KEYBOARD_BRIDGE_ENABLED = True
JOYSTICK_MOVEMENT_ENABLED = False
KEYBOARD_HOLD_FRAMES = 6
MENU_BACKGROUND_W = 160
MENU_BACKGROUND_H = 47
ACTION_CENTER_X = 79
ACTION_CENTER_Y = 59
AIM_SMOOTHING = 3


class PicoRenderer:
    def __init__(self):
        if game is None:
            raise RuntimeError("The Pico backend needs the native MicroPython module named 'game'.")
        game.init()
        self.menu_background = self._load_file(("assets/menu/background.bin", "/assets/menu/background.bin"))
        self._load_tile_sprites()
        self._load_player_sprite()

    def clear(self, color):
        game.clear(color)

    def rect(self, x, y, w, h, color):
        game.rect(x, y, w, h, color)

    def tile(self, x, y, color, top_color):
        game.tile(x, y, color, top_color)

    def tile_sprite(self, x, y, tile_id):
        game.tile_sprite(x, y, tile_id)

    def sprite8(self, x, y, sprite_id):
        game.tile_sprite(x, y, sprite_id)

    def text(self, x, y, text, color, scale=1):
        draw_text(self, x, y, text, color, scale)

    def player(self, x, y, flip_x=False):
        game.player(x, y, flip_x)

    def image(self, x, y, name, w, h):
        if name == "menu_background" and self.menu_background is not None:
            game.image(x, y, w, h, self.menu_background)

    def present(self):
        game.present()

    def _load_file(self, paths):
        for path in paths:
            try:
                with open(path, "rb") as data_file:
                    return data_file.read()
            except OSError:
                pass
        return None

    def _load_player_sprite(self):
        for path in ("assets/sprites/player_hires/player_default.bin", "/assets/sprites/player_hires/player_default.bin"):
            try:
                with open(path, "rb") as sprite_file:
                    game.load_player_sprite(sprite_file.read())
                return
            except OSError:
                pass

    def _load_tile_sprites(self):
        for sprite in sprite8_entries():
            for path in (f"assets/sprites/{sprite['file']}", f"/assets/sprites/{sprite['file']}"):
                try:
                    with open(path, "rb") as sprite_file:
                        game.load_tile_sprite(sprite["id"], sprite_file.read())
                    break
                except OSError:
                    pass


class PicoInput:
    def __init__(self):
        self.keys = Keys()
        self.kb_left = 0
        self.kb_right = 0
        self.kb_jump = 0
        self.aim_x = 0
        self.aim_y = 0
        self.stdin_poll = None
        if KEYBOARD_BRIDGE_ENABLED and sys is not None and select is not None:
            try:
                self.stdin_poll = select.poll()
                self.stdin_poll.register(sys.stdin, select.POLLIN)
            except Exception:
                self.stdin_poll = None

    def poll(self):
        self._poll_keyboard_bridge()
        self.keys.left = self.kb_left > 0
        self.keys.right = self.kb_right > 0
        self.keys.jump = self.kb_jump > 0
        if JOYSTICK_MOVEMENT_ENABLED:
            self.keys.left = self.keys.left or game.btn_left()
            self.keys.right = self.keys.right or game.btn_right()
            self.keys.jump = self.keys.jump or game.btn_jump()
        action_x = game.action_x()
        action_y = game.action_y()
        self.keys.cursor_x = action_x
        self.keys.cursor_y = action_y
        self.keys.cursor_active = False
        self.aim_x = self._smooth_axis(self.aim_x, self._scale_axis(action_x - ACTION_CENTER_X, ACTION_CENTER_X))
        self.aim_y = self._smooth_axis(self.aim_y, self._scale_axis(action_y - ACTION_CENTER_Y, ACTION_CENTER_Y))
        self.keys.aim_x = self.aim_x
        self.keys.aim_y = self.aim_y
        self.keys.dig = game.action_dig()
        self.keys.place = game.action_place()
        self._tick_keyboard_bridge()
        return self.keys

    def _scale_axis(self, value, center):
        scaled = value * 100 // center
        if scaled < -100:
            return -100
        if scaled > 100:
            return 100
        return scaled

    def _smooth_axis(self, previous, current):
        return (previous * (AIM_SMOOTHING - 1) + current) // AIM_SMOOTHING

    def _poll_keyboard_bridge(self):
        if self.stdin_poll is None:
            return
        while self.stdin_poll.poll(0):
            ch = sys.stdin.read(1)
            if ch == "L":
                self.kb_left = KEYBOARD_HOLD_FRAMES
            elif ch == "R":
                self.kb_right = KEYBOARD_HOLD_FRAMES
            elif ch == "J":
                self.kb_jump = KEYBOARD_HOLD_FRAMES

    def _tick_keyboard_bridge(self):
        if self.kb_left > 0:
            self.kb_left -= 1
        if self.kb_right > 0:
            self.kb_right -= 1
        if self.kb_jump > 0:
            self.kb_jump -= 1


def run(app):
    if game is None:
        raise RuntimeError("The Pico backend needs the native MicroPython module named 'game'.")

    renderer = PicoRenderer()
    controls = PicoInput()
    frame_ms = 33

    while True:
        start = game.ticks_ms()
        app.update(controls.poll())
        app.draw(renderer)
        elapsed = game.ticks_ms() - start
        if elapsed < frame_ms:
            game.sleep_ms(frame_ms - elapsed)
