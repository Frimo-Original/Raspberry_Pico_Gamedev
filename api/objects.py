def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def rectangles_overlap(a, b):
    return (
        a.x < b.x + b.w
        and a.x + a.w > b.x
        and a.y < b.y + b.h
        and a.y + a.h > b.y
    )


class GameObject:
    def __init__(self, x, y, w, h, color=0xFFFF):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vx = 0
        self.vy = 0
        self.color = color
        self.facing = 1
        self.state = "idle"

    def move(self):
        self.x += self.vx
        self.y += self.vy
        if self.vx < 0:
            self.facing = -1
        elif self.vx > 0:
            self.facing = 1

    def keep_inside(self, width, height):
        self.x = clamp(self.x, 0, width - self.w)
        self.y = clamp(self.y, 0, height - self.h)

    def overlaps(self, other):
        return rectangles_overlap(self, other)

    def draw(self, gfx, camera_x=0, camera_y=0):
        gfx.rect(self.x - camera_x, self.y - camera_y, self.w, self.h, self.color)
