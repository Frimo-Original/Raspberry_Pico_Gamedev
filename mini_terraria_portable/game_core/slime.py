from api import BLACK, GREEN, RED, WHITE
from .constants import MAX_FALL_SPEED, TILE


SLIME_JUMP_SPEED = -5
SLIME_MOVE_SPEED = 1
SLIME_AGGRO_MOVE_SPEED = 2
SLIME_MAX_HEALTH = 30


class Slime:
    def __init__(self, x, y, direction=-1, jump_delay=30):
        self.x = x
        self.y = y
        self.w = 8
        self.h = 6
        self.vx = 0
        self.vy = 0
        self.direction = direction
        self.jump_delay = jump_delay
        self.jump_timer = jump_delay
        self.on_ground = False
        self.max_health = SLIME_MAX_HEALTH
        self.health = self.max_health
        self.aggressive = False
        self.health_bar_timer = 0

    def update(self, world, player=None):
        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1
        if self.on_ground:
            self.vx = 0
            self.jump_timer -= 1
            if self.jump_timer <= 0:
                speed = SLIME_AGGRO_MOVE_SPEED if self.aggressive else SLIME_MOVE_SPEED
                if self.aggressive and player is not None:
                    self.direction = -1 if player.x < self.x else 1
                self.vx = self.direction * speed
                self.vy = SLIME_JUMP_SPEED
                self.on_ground = False
                self.jump_timer = max(10, self.jump_delay // 2) if self.aggressive else self.jump_delay

        self._move_x(world)
        self.vy += 1
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED
        self._move_y(world)

    def draw(self, gfx, camera_x, camera_y):
        x = self.x - camera_x
        y = self.y - camera_y
        gfx.rect(x + 1, y, self.w - 2, 1, GREEN)
        gfx.rect(x, y + 1, self.w, self.h - 1, GREEN)
        gfx.rect(x + 2, y + 2, 1, 1, BLACK)
        gfx.rect(x + 5, y + 2, 1, 1, BLACK)
        if self.health < self.max_health or self.health_bar_timer > 0:
            self._draw_health_bar(gfx, x, y + self.h + 2)

    def damage(self, amount):
        self.health -= amount
        self.aggressive = True
        self.health_bar_timer = 90
        if self.health < 0:
            self.health = 0

    def alive(self):
        return self.health > 0

    def _draw_health_bar(self, gfx, x, y):
        bar_w = self.w
        filled = bar_w * self.health // self.max_health
        gfx.rect(x, y, bar_w, 3, BLACK)
        if filled > 0:
            gfx.rect(x + 1, y + 1, max(1, filled - 2), 1, RED)
        gfx.rect(x, y - 1, bar_w, 1, WHITE)

    def _move_x(self, world):
        if self.vx == 0:
            return
        step = 1 if self.vx > 0 else -1
        for _ in range(abs(self.vx)):
            next_x = self.x + step
            if self._collides(world, next_x, self.y):
                self.direction *= -1
                self.vx = 0
                return
            self.x = next_x

    def _move_y(self, world):
        self.on_ground = False
        step = 1 if self.vy > 0 else -1
        for _ in range(abs(self.vy)):
            next_y = self.y + step
            if self._collides(world, self.x, next_y):
                if step > 0:
                    self.on_ground = True
                self.vy = 0
                return
            self.y = next_y

    def _collides(self, world, x, y):
        points = (
            (x, y),
            (x + self.w - 1, y),
            (x, y + self.h - 1),
            (x + self.w - 1, y + self.h - 1),
        )
        for px, py in points:
            if world.solid_at_pixel(px, py):
                return True
        return False

    def tile_x(self):
        return (self.x + self.w // 2) // TILE
