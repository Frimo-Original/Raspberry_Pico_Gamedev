from api import BLACK, DIRT as DIRT_COLOR
from api import OUTLINE, SKY, STONE as STONE_COLOR
from api import UI_BAR, UI_BG, UI_PANEL, WHITE
from api import SPRITE_HEART, SPRITE_HEART_25, SPRITE_HEART_50, SPRITE_HEART_75
from api import TILE_STONE, dirt_tile
from api import rectangles_overlap, text_width
from .constants import DIRT, EMPTY, SCREEN_H, SCREEN_W, STONE, TILE, WORLD_H, WORLD_W
from .player import Player
from .slime import Slime
from .world import World

RESPAWN_PROTECTION_FRAMES = 45
YELLOW = 0xFFE0
HEART_COUNT = 5
HEART_HEALTH = 20
HEALTH_QUARTER = 5
MAX_HEALTH = HEART_COUNT * HEART_HEALTH
SLIME_DAMAGE = 10
REGEN_DELAY_FRAMES = 150
REGEN_INTERVAL_FRAMES = 30
REGEN_AMOUNT = HEALTH_QUARTER
MENU_BACKGROUND_W = 160
MENU_BACKGROUND_H = 47
SELECT_REACH_TILES = 3
SELECT_DEADZONE = 16
SELECT_DISTANCE_2 = 42
SELECT_DISTANCE_3 = 68


class Game:
    def __init__(self):
        self.state = "menu"
        self.world = None
        self.player = None
        self.slimes = []
        self.camera_x = 0
        self.camera_y = 0
        self.health = MAX_HEALTH
        self.max_health = MAX_HEALTH
        self.regen_timer = 0
        self.respawn_protection_timer = 0
        self.selected_tx = None
        self.selected_ty = None
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
        self._update_health_regen()
        if self.respawn_protection_timer > 0:
            self.respawn_protection_timer -= 1
        self.frame_count += 1
        self._update_camera()
        self._update_selected_block(keys)
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
        self._draw_selected_block(gfx)
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
        self.regen_timer = 0
        self.respawn_protection_timer = 0
        self.camera_x = 0
        self.camera_y = 0
        self.frame_count = 0
        self.state = "playing"

    def _draw_menu(self, gfx):
        gfx.clear(UI_BG)
        gfx.image((SCREEN_W - MENU_BACKGROUND_W) // 2, 6, "menu_background", MENU_BACKGROUND_W, MENU_BACKGROUND_H)
        gfx.rect(24, 76, 112, 34, UI_PANEL)
        gfx.rect(34, 86, 92, 14, UI_BAR)
        gfx.rect(38, 90, 84, 6, WHITE)
        gfx.text((SCREEN_W - text_width("START", 2)) // 2, 89, "START", BLACK, 2)

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
        # Пока только выбираем блок. Ломание и постановку подключим после инвентаря.
        self.last_dig = keys.dig
        self.last_place = keys.place

    def _update_selected_block(self, keys):
        target = self._joystick_target(keys)
        if target is None and keys.cursor_active:
            tx = (keys.cursor_x + self.camera_x) // TILE
            ty = (keys.cursor_y + self.camera_y) // TILE
            if self._block_in_select_range(tx, ty):
                target = (tx, ty)
        if target is None or self._block_inside_player(target[0], target[1]):
            self.selected_tx = None
            self.selected_ty = None
        else:
            self.selected_tx, self.selected_ty = target

    def _joystick_target(self, keys):
        dx = self._axis_to_tile_offset(keys.aim_x)
        dy = self._axis_to_tile_offset(keys.aim_y)
        if dx == 0 and dy == 0:
            return None

        left, right, top, bottom = self._player_tile_bounds()
        tx = (left + right) // 2 + dx
        ty = bottom + dy
        if 0 <= tx < WORLD_W and 0 <= ty < WORLD_H:
            return tx, ty
        return None

    def _axis_to_tile_offset(self, value):
        sign = 1
        if value < 0:
            sign = -1
            value = -value
        if value <= SELECT_DEADZONE:
            return 0
        if value < SELECT_DISTANCE_2:
            return sign
        if value < SELECT_DISTANCE_3:
            return sign * 2
        return sign * SELECT_REACH_TILES

    def _player_tile_bounds(self):
        left = self.player.x // TILE
        right = (self.player.x + self.player.w - 1) // TILE
        top = self.player.y // TILE
        bottom = (self.player.y + self.player.h - 1) // TILE
        return left, right, top, bottom

    def _block_in_select_range(self, tx, ty):
        left, right, top, bottom = self._player_tile_bounds()
        return (
            left - SELECT_REACH_TILES <= tx <= right + SELECT_REACH_TILES
            and top - SELECT_REACH_TILES <= ty <= bottom + SELECT_REACH_TILES
        )

    def _block_inside_player(self, tx, ty):
        left, right, top, bottom = self._player_tile_bounds()
        return left <= tx <= right and top <= ty <= bottom

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
                elif tile == STONE:
                    gfx.tile_sprite(x, y, TILE_STONE)
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
        self.health -= SLIME_DAMAGE
        self.regen_timer = 0
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
        self.regen_timer = 0
        self.respawn_protection_timer = RESPAWN_PROTECTION_FRAMES
        self._update_camera()

    def _update_health_regen(self):
        if self.health <= 0 or self.health >= self.max_health:
            self.regen_timer = 0
            return
        self.regen_timer += 1
        if self.regen_timer < REGEN_DELAY_FRAMES:
            return
        if (self.regen_timer - REGEN_DELAY_FRAMES) % REGEN_INTERVAL_FRAMES == 0:
            self.health += REGEN_AMOUNT
            if self.health > self.max_health:
                self.health = self.max_health

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

    def _draw_selected_block(self, gfx):
        if self.selected_tx is None or self.selected_ty is None:
            return
        x = self.selected_tx * TILE - self.camera_x
        y = self.selected_ty * TILE - self.camera_y
        if x <= -TILE or x >= SCREEN_W or y <= -TILE or y >= SCREEN_H:
            return
        gfx.rect(x, y, TILE, 1, YELLOW)
        gfx.rect(x, y + TILE - 1, TILE, 1, YELLOW)
        gfx.rect(x, y, 1, TILE, YELLOW)
        gfx.rect(x + TILE - 1, y, 1, TILE, YELLOW)

    def _draw_hud(self, gfx):
        gap = 1
        heart_size = 8
        total_w = HEART_COUNT * heart_size + (HEART_COUNT - 1) * gap
        x = SCREEN_W - total_w - 2
        y = 2
        for index in range(HEART_COUNT):
            heart_health = self.health - (HEART_COUNT - 1 - index) * HEART_HEALTH
            sprite = self._heart_sprite(heart_health)
            if sprite >= 0:
                gfx.sprite8(x + index * (heart_size + gap), y, sprite)

    def _heart_sprite(self, heart_health):
        if heart_health >= HEART_HEALTH:
            return SPRITE_HEART
        if heart_health >= 15:
            return SPRITE_HEART_75
        if heart_health >= 10:
            return SPRITE_HEART_50
        if heart_health >= HEALTH_QUARTER:
            return SPRITE_HEART_25
        return -1

    def _tile_color(self, tile):
        if tile == DIRT:
            return DIRT_COLOR
        if tile == STONE:
            return STONE_COLOR
        return BLACK
