from api import GameObject, BLACK, GREEN, RED, SKY, WHITE


WIDTH = 160
HEIGHT = 120


class CatchGiftGame:
    def __init__(self):
        self.player = GameObject(WIDTH // 2 - 10, HEIGHT - 12, 20, 6, GREEN)
        self.gift = GameObject(20, 0, 8, 8, RED)
        self.score = 0
        self.missed = 0

    def update(self, keys):
        self.player.vx = 0
        if keys.left:
            self.player.vx = -3
        if keys.right:
            self.player.vx = 3
        self.player.move()
        self.player.keep_inside(WIDTH, HEIGHT)

        self.gift.vy = 2
        self.gift.move()

        if self.player.overlaps(self.gift):
            self.score += 1
            self._reset_gift()
        elif self.gift.y > HEIGHT:
            self.missed += 1
            self._reset_gift()

    def draw(self, gfx):
        gfx.clear(SKY)
        self.player.draw(gfx)
        self.gift.draw(gfx)
        self._draw_score(gfx)
        gfx.present()

    def _reset_gift(self):
        self.gift.x = (self.gift.x * 37 + 23) % (WIDTH - self.gift.w)
        self.gift.y = 0
        self.gift.vy = 0

    def _draw_score(self, gfx):
        for i in range(self.score % 10):
            gfx.rect(2 + i * 4, 2, 3, 3, WHITE)
        for i in range(self.missed % 10):
            gfx.rect(2 + i * 4, 7, 3, 3, BLACK)


if __name__ == "__main__":
    from backends.tkinter_backend import run

    run(CatchGiftGame())
