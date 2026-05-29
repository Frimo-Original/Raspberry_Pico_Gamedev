from api import SpriteState
from .constants import JUMP_SPEED, MAX_FALL_SPEED, MOVE_SPEED, TILE


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 7
        self.h = 12
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.facing = -1
        self.state = SpriteState.IDLE

    def update(self, keys, world):
        self.vx = 0
        if keys.left:
            self.vx -= MOVE_SPEED
        if keys.right:
            self.vx += MOVE_SPEED
        if self.vx < 0:
            self.facing = -1
        elif self.vx > 0:
            self.facing = 1
        if keys.jump and self.on_ground:
            self.vy = JUMP_SPEED
            self.on_ground = False

        self._move_x(world)
        self.vy += 1
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED
        self._move_y(world)
        self._update_state()

    def _update_state(self):
        if not self.on_ground:
            self.state = SpriteState.JUMP
        elif self.vx != 0:
            self.state = SpriteState.WALK
        else:
            self.state = SpriteState.IDLE

    def _move_x(self, world):
        step = 1 if self.vx > 0 else -1
        for _ in range(abs(self.vx)):
            next_x = self.x + step
            if self._collides(world, next_x, self.y):
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

    def tile_y(self):
        return (self.y + self.h // 2) // TILE
