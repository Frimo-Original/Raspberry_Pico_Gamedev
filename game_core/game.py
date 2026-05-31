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
SELECT_DEADZONE = 18
SELECT_DISTANCE_2 = 48
SELECT_DISTANCE_3 = 76
HOTBAR_SLOTS = 6
HOTBAR_SLOT = 10
HOTBAR_GAP = 1
HOTBAR_X = 2
HOTBAR_Y = 2
HOTBAR_SELECT_THRESHOLD = 35
HOTBAR_SELECT_RELEASE = 18
ITEM_SWORD = 0
ITEM_PICKAXE = 1
ITEM_DIRT = 2
ITEM_STONE = 3
ITEM_SWING_FRAMES = 6
ITEM_SWING_FRAME_TICKS = 3
ITEM_FRAME_SIZE = 32
ITEM_RIGHT_PIVOT_X = 10
ITEM_LEFT_PIVOT_X = 21
ITEM_PIVOT_Y = 22
SWORD_DAMAGE = 10
SWORD_HIT_W = 18
SWORD_HIT_H = 18
DIG_TIME_DIRT = 24
DIG_TIME_STONE = 70
DIG_SWING_EVERY = 14


class HitBox:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


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
        self.hotbar_selected = 0
        self.hotbar_select_mode = False
        self.hotbar_candidate = 0
        self.hotbar_axis_lock = 0
        self.item_swing_frame = -1
        self.item_swing_tick = 0
        self.item_swing_name = ""
        self.sword_hit_done = False
        self.dig_tx = None
        self.dig_ty = None
        self.dig_progress = 0
        self.dig_total = 0
        self.dig_swing_timer = 0
        self.last_dig = False
        self.last_place = False
        self.frame_count = 0

    def update(self, keys):
        if self.state == "menu":
            if keys.any_button:
                self._start_loading()
            return
        if self.state == "loading":
            if self.world.generate_step():
                self._start_playing()
            return

        self._update_hotbar_selection(keys)
        if self.hotbar_select_mode:
            keys.left = False
            keys.right = False
            keys.up = False
            keys.down = False
            keys.button_a = False
            keys.button_b = False
        self.player.update(keys, self.world)
        self._update_slimes()
        self._check_enemy_hits()
        self._update_health_regen()
        if self.respawn_protection_timer > 0:
            self.respawn_protection_timer -= 1
        self.frame_count += 1
        self._update_camera()
        self._update_selected_block(keys)
        self._update_pickaxe_dig(keys)
        self._update_item_swing(keys)
        self._check_sword_hits()
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
        self._draw_item_swing(gfx)
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
        # Keep edge-triggered actions stable between frames.
        self.last_dig = keys.button_a
        self.last_place = keys.button_b

    def _update_hotbar_selection(self, keys):
        if keys.button_menu:
            if self.hotbar_select_mode:
                self.hotbar_selected = self.hotbar_candidate
                self.hotbar_select_mode = False
                self.hotbar_axis_lock = 0
            else:
                self.hotbar_candidate = self.hotbar_selected
                self.hotbar_select_mode = True
                self.hotbar_axis_lock = 0
        if not self.hotbar_select_mode:
            return

        axis = keys.axis_x
        if -HOTBAR_SELECT_RELEASE <= axis <= HOTBAR_SELECT_RELEASE:
            self.hotbar_axis_lock = 0
            return
        direction = 0
        if axis >= HOTBAR_SELECT_THRESHOLD:
            direction = 1
        elif axis <= -HOTBAR_SELECT_THRESHOLD:
            direction = -1
        if direction != 0 and direction != self.hotbar_axis_lock:
            self.hotbar_candidate += direction
            if self.hotbar_candidate < 0:
                self.hotbar_candidate = HOTBAR_SLOTS - 1
            elif self.hotbar_candidate >= HOTBAR_SLOTS:
                self.hotbar_candidate = 0
            self.hotbar_axis_lock = direction

    def _update_item_swing(self, keys):
        item_name = self._current_swing_item()
        if item_name and item_name != "copper_pickaxe" and keys.button_a and not self.last_dig:
            self._start_item_swing(item_name)
        if self.item_swing_frame < 0:
            return
        self.item_swing_tick += 1
        if self.item_swing_tick >= ITEM_SWING_FRAME_TICKS:
            self.item_swing_tick = 0
            self.item_swing_frame += 1
            if self.item_swing_frame >= ITEM_SWING_FRAMES:
                self.item_swing_frame = -1
                self.item_swing_name = ""
                self.sword_hit_done = False

    def _current_swing_item(self):
        if self.hotbar_selected == ITEM_SWORD:
            return "copper_sword"
        if self.hotbar_selected == ITEM_PICKAXE:
            return "copper_pickaxe"
        return ""

    def _start_item_swing(self, item_name):
        self.item_swing_name = item_name
        self.item_swing_frame = 0
        self.item_swing_tick = 0
        if item_name == "copper_sword":
            self.sword_hit_done = False

    def _update_pickaxe_dig(self, keys):
        if self.hotbar_selected != ITEM_PICKAXE or not keys.button_a:
            self._reset_dig_progress()
            return
        if self.selected_tx is None or self.selected_ty is None:
            self._reset_dig_progress()
            return

        tile = self.world.get(self.selected_tx, self.selected_ty)
        total = self._dig_time(tile)
        if total <= 0:
            self._reset_dig_progress()
            return

        if self.dig_tx != self.selected_tx or self.dig_ty != self.selected_ty:
            self.dig_tx = self.selected_tx
            self.dig_ty = self.selected_ty
            self.dig_progress = 0
            self.dig_total = total
            self.dig_swing_timer = 0

        self.dig_total = total
        self.dig_progress += 1
        self.dig_swing_timer -= 1
        if self.dig_swing_timer <= 0:
            self._start_item_swing("copper_pickaxe")
            self.dig_swing_timer = DIG_SWING_EVERY

        if self.dig_progress >= self.dig_total:
            self.world.set(self.dig_tx, self.dig_ty, EMPTY)
            self._reset_dig_progress()

    def _dig_time(self, tile):
        if tile == DIRT:
            return DIG_TIME_DIRT
        if tile == STONE:
            return DIG_TIME_STONE
        return 0

    def _reset_dig_progress(self):
        self.dig_tx = None
        self.dig_ty = None
        self.dig_progress = 0
        self.dig_total = 0
        self.dig_swing_timer = 0

    def _check_sword_hits(self):
        if self.item_swing_name != "copper_sword" or self.item_swing_frame < 0 or self.sword_hit_done:
            return
        hitbox = self._sword_hitbox()
        for slime in self.slimes:
            if slime.alive() and rectangles_overlap(hitbox, slime):
                slime.damage(SWORD_DAMAGE)
                self.sword_hit_done = True
                break
        self.slimes = [slime for slime in self.slimes if slime.alive()]

    def _sword_hitbox(self):
        if self.player.facing > 0:
            x = self.player.x + self.player.w - 1
        else:
            x = self.player.x - SWORD_HIT_W + 1
        y = self.player.y - 4
        return HitBox(x, y, SWORD_HIT_W, SWORD_HIT_H)

    def _update_selected_block(self, keys):
        if self.hotbar_select_mode:
            self.selected_tx = None
            self.selected_ty = None
            return
        target = self._joystick_target(keys)
        if target is None and keys.pointer_active:
            tx = (keys.pointer_x + self.camera_x) // TILE
            ty = (keys.pointer_y + self.camera_y) // TILE
            if self._block_in_select_range(tx, ty):
                target = (tx, ty)
        if target is None or self._block_inside_player(target[0], target[1]):
            self.selected_tx = None
            self.selected_ty = None
        else:
            self.selected_tx, self.selected_ty = target

    def _joystick_target(self, keys):
        dx = self._axis_to_tile_offset(keys.axis_x)
        dy = self._axis_to_tile_offset(keys.axis_y)
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

    def _draw_item_swing(self, gfx):
        if self.item_swing_frame < 0 or not self.item_swing_name:
            return
        player_x = self.player.x - self.camera_x
        player_y = self.player.y - self.camera_y
        hand_y = player_y + 6
        if self.player.facing > 0:
            side = "r"
            hand_x = player_x + self.player.w
            x = hand_x - ITEM_RIGHT_PIVOT_X
        else:
            side = "l"
            hand_x = player_x
            x = hand_x - ITEM_LEFT_PIVOT_X
        y = hand_y - ITEM_PIVOT_Y
        gfx.image(x, y, f"{self.item_swing_name}_swing_{side}_{self.item_swing_frame}", ITEM_FRAME_SIZE, ITEM_FRAME_SIZE)

    def _check_enemy_hits(self):
        if self.respawn_protection_timer > 0:
            return
        for slime in self.slimes:
            if slime.alive() and rectangles_overlap(self.player, slime):
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
                slime.update(self.world, self.player)

    def _draw_slimes(self, gfx):
        left = self.camera_x - 12
        right = self.camera_x + SCREEN_W + 12
        for slime in self.slimes:
            if slime.alive() and left <= slime.x <= right:
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
        if self.dig_tx == self.selected_tx and self.dig_ty == self.selected_ty and self.dig_total > 0:
            filled = (TILE - 2) * self.dig_progress // self.dig_total
            gfx.rect(x + 1, y + TILE - 3, TILE - 2, 2, BLACK)
            if filled > 0:
                gfx.rect(x + 1, y + TILE - 3, filled, 2, UI_BAR)

    def _draw_hud(self, gfx):
        self._draw_hotbar(gfx)
        self._draw_hearts(gfx)

    def _draw_hotbar(self, gfx):
        hotbar_w = HOTBAR_SLOTS * HOTBAR_SLOT + (HOTBAR_SLOTS - 1) * HOTBAR_GAP
        if self.hotbar_select_mode:
            gfx.rect(HOTBAR_X, HOTBAR_Y + HOTBAR_SLOT + 1, hotbar_w, 2, UI_BAR)
        for slot in range(HOTBAR_SLOTS):
            x = HOTBAR_X + slot * (HOTBAR_SLOT + HOTBAR_GAP)
            y = HOTBAR_Y
            active_slot = self.hotbar_candidate if self.hotbar_select_mode else self.hotbar_selected
            border = YELLOW if slot == active_slot else WHITE
            if self.hotbar_select_mode and slot == self.hotbar_selected and slot != active_slot:
                border = UI_BAR
            gfx.rect(x, y, HOTBAR_SLOT, HOTBAR_SLOT, border)
            gfx.rect(x + 1, y + 1, HOTBAR_SLOT - 2, HOTBAR_SLOT - 2, UI_PANEL)
            if slot == ITEM_SWORD:
                gfx.image(x + 1, y + 1, "copper_sword_icon", 8, 8)
            elif slot == ITEM_PICKAXE:
                gfx.image(x + 1, y + 1, "copper_pickaxe_icon", 8, 8)
            elif slot == ITEM_DIRT:
                gfx.tile_sprite(x + 1, y + 1, dirt_tile(False))
            elif slot == ITEM_STONE:
                gfx.tile_sprite(x + 1, y + 1, TILE_STONE)
            elif slot == HOTBAR_SLOTS - 1:
                self._draw_inventory_slot_icon(gfx, x + 1, y + 1)

    def _draw_inventory_slot_icon(self, gfx, x, y):
        gfx.rect(x + 1, y + 1, 6, 1, WHITE)
        gfx.rect(x + 1, y + 3, 6, 1, WHITE)
        gfx.rect(x + 1, y + 5, 6, 1, WHITE)

    def _draw_hearts(self, gfx):
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
