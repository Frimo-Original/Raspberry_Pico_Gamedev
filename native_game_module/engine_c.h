#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void engine_init(void);
void engine_clear(uint16_t color);
void engine_rect(int x, int y, int w, int h, uint16_t color);
void engine_tile(int x, int y, uint16_t color, uint16_t top_color);
bool engine_load_tile_sprite(int tile_id, const uint8_t *data, uint32_t len);
void engine_tile_sprite(int x, int y, int tile_id);
bool engine_image(int x, int y, int w, int h, const uint8_t *data, uint32_t len);
bool engine_load_player_sprite(const uint8_t *data, uint32_t len);
void engine_player(int x, int y, bool flip_x);
void engine_present(void);
bool engine_btn_left(void);
bool engine_btn_right(void);
bool engine_btn_jump(void);
int engine_action_x(void);
int engine_action_y(void);
bool engine_action_dig(void);
bool engine_action_place(void);
uint32_t engine_ticks_ms(void);
void engine_sleep_ms(uint32_t ms);
uint32_t engine_frame_ms(void);
uint32_t engine_fps(void);
uint32_t engine_spi_baudrate(void);

#ifdef __cplusplus
}
#endif
