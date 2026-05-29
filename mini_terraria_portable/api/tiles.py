BLOCK_AIR = 0
BLOCK_DIRT = 1
BLOCK_STONE = 2

from .assets import sprite8_id


TILE_DIRT = sprite8_id("tile", "dirt")
TILE_GRASS = sprite8_id("tile", "grass")
TILE_STONE = sprite8_id("tile", "stone")
SPRITE_HEART = sprite8_id("item", "heart")
SPRITE_HEART_75 = sprite8_id("item", "heart_75")
SPRITE_HEART_50 = sprite8_id("item", "heart_50")
SPRITE_HEART_25 = sprite8_id("item", "heart_25")


def is_solid(block):
    return block != BLOCK_AIR


def dirt_tile(has_air_above):
    if has_air_above:
        return TILE_GRASS
    return TILE_DIRT
