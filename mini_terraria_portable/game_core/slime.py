from api import BLACK, GREEN
from .constants import MAX_FALL_SPEED, TILE


SLIME_JUMP_SPEED = -5
SLIME_MOVE_SPEED = 1


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

    def update(self, world):
        if self.on_ground:
            self.vx = 0
            self.jump_timer -= 1
            if self.jump_timer <= 0:
                self.vx = self.direction * SLIME_MOVE_SPEED
                self.vy = SLIME_JUMP_SPEED
                self.on_ground = False
                self.jump_timer = self.jump_delay

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
