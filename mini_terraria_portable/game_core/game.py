from api import BLACK, DIRT as DIRT_COLOR
from api import OUTLINE, SKY, STONE as STONE_COLOR
from api import UI_BAR, UI_BG, UI_PANEL, WHITE
from api import SPRITE_HEART, dirt_tile
from api import rectangles_overlap, text_width
from .constants import DIRT, EMPTY, SCREEN_H, SCREEN_W, STONE, TILE, WORLD_H, WORLD_W
from .player import Player
from .slime import Slime
from .world import World

RESPAWN_PROTECTION_FRAMES = 45


class Game:
    def __init__(self):
        self.state = "menu"
        self.world = None
        self.player = None
        self.slimes = []
        self.camera_x = 0
        self.camera_y = 0
        self.health = 5
        self.max_health = 5
        self.respawn_protection_timer = 0
        self.last_dig = False
        self.last_place = False
        self.frame_count = 0

    def update(self, keys):
        if self.state == "menu":
            if keys.action:
                self._start_loading()
            return
        if self.state == "loading":
            if self.world.generate_step():
                self._start_playing()
            return

        self.player.update(keys, self.world)
        self._update_slimes()
        self._check_enemy_hits()
        if self.respawn_protection_timer > 0:
            self.respawn_protection_timer -= 1
        self.frame_count += 1
        self._update_camera()
        self._edit_world(keys)

    def draw(self, gfx):
        if self.state == "menu":
            self._draw_menu(gfx)
            gfx.present()
            return
        if self.state == "loading":
            self._draw_loading(gfx)
            gfx.present()
            return

        gfx.clear(SKY)
        self._draw_tiles(gfx)
        self._draw_slimes(gfx)
        self._draw_player(gfx)
        self._draw_hud(gfx)
        gfx.present()

    def _start_loading(self):
        self.world = World(auto_generate=False)
        self.state = "loading"

    def _start_playing(self):
        self.player = Player(*self.world.spawn_position())
        self.slimes = self._make_slimes()
        self.health = self.max_health
        self.respawn_protection_timer = 0
        self.camera_x = 0
        self.camera_y = 0
        self.frame_count = 0
        self.state = "playing"

    def _draw_menu(self, gfx):
        gfx.clear(UI_BG)
        gfx.rect(24, 34, 112, 34, UI_PANEL)
        gfx.rect(34, 44, 92, 14, UI_BAR)
        gfx.rect(38, 48, 84, 6, WHITE)
        gfx.text((SCREEN_W - text_width("START", 2)) // 2, 47, "START", BLACK, 2)

    def _draw_loading(self, gfx):
        gfx.clear(UI_BG)
        gfx.text((SCREEN_W - text_width("LOADING", 1)) // 2, 42, "LOADING", WHITE)
        current, total = self.world.generation_progress()
        bar_w = 104
        bar_h = 10
        filled = bar_w * current // total
        if filled < 0:
            filled = 0
        if filled > bar_w:
            filled = bar_w
        x = (SCREEN_W - bar_w) // 2
        y = 55
        gfx.rect(x - 1, y - 1, bar_w + 2, bar_h + 2, WHITE)
        gfx.rect(x, y, bar_w, bar_h, UI_PANEL)
        if filled > 0:
            gfx.rect(x, y, filled, bar_h, UI_BAR)

    def _update_camera(self):
        max_x = WORLD_W * TILE - SCREEN_W
        max_y = WORLD_H * TILE - SCREEN_H
        self.camera_x = self.player.x - SCREEN_W // 2
        self.camera_y = self.player.y - SCREEN_H // 2
        if self.camera_x < 0:
            self.camera_x = 0
        if self.camera_y < 0:
            self.camera_y = 0
        if self.camera_x > max_x:
            self.camera_x = max_x
        if self.camera_y > max_y:
            self.camera_y = max_y

    def _edit_world(self, keys):
        tx = (keys.cursor_x + self.camera_x) // TILE
        ty = (keys.cursor_y + self.camera_y) // TILE

        if keys.dig and not self.last_dig:
            self.world.set(tx, ty, EMPTY)
        if keys.place and not self.last_place:
            if self.world.get(tx, ty) == EMPTY:
                self.world.set(tx, ty, DIRT)

        self.last_dig = keys.dig
        self.last_place = keys.place

    def _draw_tiles(self, gfx):
        first_x = self.camera_x // TILE
        first_y = self.camera_y // TILE
        off_x = self.camera_x % TILE
        off_y = self.camera_y % TILE
        cols = SCREEN_W // TILE + 2
        rows = SCREEN_H // TILE + 2
        world = self.world
        tiles = world.tiles

        for row in range(rows):
            ty = first_y + row
            if ty < 0 or ty >= WORLD_H:
                continue
            row_base = ty * WORLD_W
            above_base = (ty - 1) * WORLD_W
            for col in range(cols):
                tx = first_x + col
                if tx < 0 or tx >= WORLD_W:
                    tile = STONE
                else:
                    tile = tiles[row_base + tx]
                if tile == EMPTY:
                    continue
                x = col * TILE - off_x
                y = row * TILE - off_y
                if tile == DIRT:
                    has_grass = False
                    if ty > 0 and 0 <= tx < WORLD_W:
                        has_grass = tiles[above_base + tx] == EMPTY
                    gfx.tile_sprite(x, y, dirt_tile(has_grass))
                else:
                    gfx.tile(x, y, self._tile_color(tile), OUTLINE)

    def _draw_player(self, gfx):
        if self.respawn_protection_timer > 0 and (self.respawn_protection_timer // 5) % 2 == 0:
            return
        x = self.player.x - self.camera_x
        y = self.player.y - self.camera_y
        gfx.player(x, y - 4, flip_x=self.player.facing > 0)

    def _check_enemy_hits(self):
        if self.respawn_protection_timer > 0:
            return
        for slime in self.slimes:
            if rectangles_overlap(self.player, slime):
                self._damage_player(slime)
                return

    def _damage_player(self, enemy):
        self.health -= 1
        if self.health <= 0:
            self._respawn_player()
            return

        player_center = self.player.x + self.player.w // 2
        enemy_center = enemy.x + enemy.w // 2
        if player_center < enemy_center:
            self.player.knockback(-2, -5)
        else:
            self.player.knockback(2, -5)

    def _respawn_player(self):
        self.player = Player(*self.world.spawn_position())
        self.health = self.max_health
        self.respawn_protection_timer = RESPAWN_PROTECTION_FRAMES
        self._update_camera()

    def _make_slimes(self):
        result = []
        for index, tile_x in enumerate((18, 38, 62, 92, 126, 165)):
            if tile_x >= WORLD_W:
                continue
            surface_y = self.world.surface[tile_x]
            direction = -1 if index % 2 == 0 else 1
            delay = 24 + index * 7
            result.append(Slime(tile_x * TILE, surface_y * TILE - 6, direction, delay))
        return result

    def _update_slimes(self):
        first_visible = self.camera_x // TILE - 4
        last_visible = (self.camera_x + SCREEN_W) // TILE + 4
        for slime in self.slimes:
            tile_x = slime.tile_x()
            if first_visible <= tile_x <= last_visible:
                slime.update(self.world)

    def _draw_slimes(self, gfx):
        left = self.camera_x - 12
        right = self.camera_x + SCREEN_W + 12
        for slime in self.slimes:
            if left <= slime.x <= right:
                slime.draw(gfx, self.camera_x, self.camera_y)

    def _draw_hud(self, gfx):
        gap = 1
        heart_size = 8
        total_w = self.max_health * heart_size + (self.max_health - 1) * gap
        x = SCREEN_W - total_w - 2
        y = 2
        for index in range(self.health):
            gfx.sprite8(x + index * (heart_size + gap), y, SPRITE_HEART)

    def _tile_color(self, tile):
        if tile == DIRT:
            return DIRT_COLOR
        if tile == STONE:
            return STONE_COLOR
        return BLACK
