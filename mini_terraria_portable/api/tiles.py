BLOCK_AIR = 0
BLOCK_DIRT = 1
BLOCK_STONE = 2

TILE_DIRT = 0
TILE_GRASS = 1
SPRITE_HEART = 2


def is_solid(block):
    return block != BLOCK_AIR


def dirt_tile(has_air_above):
    if has_air_above:
        return TILE_GRASS
    return TILE_DIRT
