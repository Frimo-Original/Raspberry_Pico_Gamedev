from api.keys import Keys

try:
    import game
except ImportError:
    game = None


class PicoRenderer:
    def __init__(self):
        if game is None:
            raise RuntimeError("The Pico backend needs the native MicroPython module named 'game'.")
        game.init()
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

    def player(self, x, y, flip_x=False):
        game.player(x, y, flip_x)

    def present(self):
        game.present()

    def _load_player_sprite(self):
        for path in ("assets/sprites/player_hires/player_default.bin", "/assets/sprites/player_hires/player_default.bin"):
            try:
                with open(path, "rb") as sprite_file:
                    game.load_player_sprite(sprite_file.read())
                return
            except OSError:
                pass

    def _load_tile_sprites(self):
        for tile_id, name in ((0, "dirt"), (1, "grass")):
            for path in (f"assets/sprites/tiles/{name}.bin", f"/assets/sprites/tiles/{name}.bin"):
                try:
                    with open(path, "rb") as sprite_file:
                        game.load_tile_sprite(tile_id, sprite_file.read())
                    break
                except OSError:
                    pass
        for path in ("assets/sprites/items/heart.bin", "/assets/sprites/items/heart.bin"):
            try:
                with open(path, "rb") as sprite_file:
                    game.load_tile_sprite(2, sprite_file.read())
                return
            except OSError:
                pass


class PicoInput:
    def __init__(self):
        self.keys = Keys()

    def poll(self):
        self.keys.left = game.btn_left()
        self.keys.right = game.btn_right()
        self.keys.jump = game.btn_jump()
        self.keys.cursor_x = game.action_x()
        self.keys.cursor_y = game.action_y()
        self.keys.dig = game.action_dig()
        self.keys.place = game.action_place()
        return self.keys


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
