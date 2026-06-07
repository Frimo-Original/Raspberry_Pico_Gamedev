from .constants import DIRT, EMPTY, STONE, TILE, WORLD_H, WORLD_W


GEN_ROWS_PER_STEP = 4
CAVE_TUNNEL_COUNT = 3
CAVE_BRANCH_COUNT = 5


class World:
    def __init__(self, seed=7, auto_generate=True):
        self.seed = seed
        self.surface = []
        self.caves = bytearray(WORLD_W * WORLD_H)
        self.tiles = bytearray(WORLD_W * WORLD_H)
        self.generation_step = 0
        self.generation_row = 0
        self.generation_done = False
        self.generation_total_steps = WORLD_H + 2
        self.generation_done_steps = 0
        if auto_generate:
            while not self.generation_done:
                self.generate_step()

    def generate_step(self):
        if self.generation_done:
            return True
        if self.generation_step == 0:
            self.surface = self._make_surface()
            self._make_caves()
            self.generation_done_steps += 1
            self.generation_step = 1
            return False
        if self.generation_step == 1:
            if self._generate_rows():
                self.generation_step = 2
            return False
        if self.generation_step == 2:
            self._clear_spawn_area()
            self.caves = None
            self.generation_done_steps += 1
            self.generation_done = True
            return True
        self.generation_done = True
        return True

    def generation_progress(self):
        if self.generation_done:
            return 1, 1
        if self.generation_done_steps > self.generation_total_steps:
            return self.generation_total_steps, self.generation_total_steps
        return self.generation_done_steps, self.generation_total_steps

    def generation_status(self):
        if self.generation_done:
            return "Готово"
        if self.generation_step == 0:
            return "Рисуем холмы"
        if self.generation_step == 1:
            return "Генерируем мир"
        return "Готовим старт"

    def get(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty < 0 or ty >= WORLD_H:
            return STONE
        return self.tiles[self._index(tx, ty)]

    def set(self, tx, ty, tile):
        if 0 <= tx < WORLD_W and 0 <= ty < WORLD_H:
            self.tiles[self._index(tx, ty)] = tile

    def solid_at_pixel(self, px, py):
        if py < 0:
            return False
        return self.get(px // TILE, py // TILE) != EMPTY

    def spawn_position(self):
        x = 3
        return x * TILE, self.surface[x] * TILE - 12

    def memory_bytes(self):
        return len(self.tiles)

    def loaded_chunk_count(self):
        return 0

    def update_around_pixel(self, _px):
        pass

    def load_background_step(self):
        return False

    def _generate_rows(self):
        for _ in range(GEN_ROWS_PER_STEP):
            if self.generation_row >= WORLD_H:
                return True
            self._fill_row(self.generation_row)
            self.generation_row += 1
            self.generation_done_steps += 1
        return self.generation_row >= WORLD_H

    def _fill_row(self, y):
        row_base = y * WORLD_W
        for x in range(WORLD_W):
            self.tiles[row_base + x] = self._generated_tile(x, y)

    def _generated_tile(self, x, y):
        return self._base_tile(x, y)

    def _base_tile(self, x, y):
        ground = self.surface[x]
        dirt_depth = 4 + self._rand(x, 4, 3)
        if y < ground:
            return EMPTY
        if self.caves[self._index(x, y)]:
            return EMPTY
        if y < ground + dirt_depth:
            return DIRT
        return STONE

    def _clear_spawn_area(self):
        x = 3
        ground = self.surface[x]
        for y in range(max(0, ground - 4), ground):
            for sx in range(1, 6):
                self.tiles[self._index(sx, y)] = EMPTY
        for sx in range(1, 6):
            self.tiles[self._index(sx, ground)] = DIRT

    def _make_surface(self):
        height = 14
        surface = []
        for x in range(WORLD_W):
            roll = self._rand(x, 0, 3)
            if roll == 0:
                height -= 1
            elif roll == 2:
                height += 1
            height = self._clamp(height, 9, min(18, WORLD_H - 8))
            surface.append(height)

        for _ in range(2):
            smoothed = surface[:]
            for x in range(1, WORLD_W - 1):
                smoothed[x] = (surface[x - 1] + surface[x] + surface[x + 1]) // 3
            surface = smoothed
        return surface

    def _make_caves(self):
        spacing = WORLD_W // (CAVE_TUNNEL_COUNT + 1)
        for tunnel_index in range(CAVE_TUNNEL_COUNT):
            entrance_x = spacing * (tunnel_index + 1)
            entrance_x += self._rand(tunnel_index, 91, 9) - 4
            entrance_x = self._clamp(entrance_x, 10, WORLD_W - 6)

            center_x = entrance_x
            start_y = self.surface[entrance_x]
            for y in range(start_y, WORLD_H):
                if y > start_y and y % 3 == 0:
                    center_x += self._rand(tunnel_index * 17 + y, 73, 3) - 1
                    center_x = self._clamp(center_x, 2, WORLD_W - 3)
                radius = 1 if y < start_y + 6 else 2
                self._carve_circle(center_x, y, radius)

        for branch_index in range(CAVE_BRANCH_COUNT):
            y = 20 + self._rand(branch_index, 121, max(1, WORLD_H - 24))
            x = 4 + self._rand(branch_index, 133, 12)
            direction = 1
            length = WORLD_W - 8
            for step in range(length):
                if step > 0 and step % 5 == 0:
                    y += self._rand(branch_index * 31 + step, 149, 3) - 1
                    y = self._clamp(y, 18, WORLD_H - 3)
                radius = 1 + self._rand(branch_index, step + 181, 2)
                self._carve_circle(x, y, radius)
                x += direction
                if x >= WORLD_W - 4:
                    break

    def _carve_circle(self, center_x, center_y, radius):
        radius_squared = radius * radius + 1
        for y in range(center_y - radius, center_y + radius + 1):
            if y < 0 or y >= WORLD_H:
                continue
            for x in range(center_x - radius, center_x + radius + 1):
                if x < 0 or x >= WORLD_W:
                    continue
                dx = x - center_x
                dy = y - center_y
                if dx * dx + dy * dy <= radius_squared:
                    self.caves[self._index(x, y)] = 1

    def _rand(self, x, y, maximum):
        value = x * 374761393 + y * 668265263 + self.seed * 982451653
        value = (value ^ (value >> 13)) * 1274126177
        value = value ^ (value >> 16)
        return (value & 0x7FFFFFFF) % maximum

    def _clamp(self, value, low, high):
        if value < low:
            return low
        if value > high:
            return high
        return value

    def _index(self, x, y):
        return y * WORLD_W + x
