#pragma once

#include <stdint.h>

void ili9341_init(void);
void ili9341_fill_rect(int x, int y, int w, int h, uint16_t color);
void ili9341_draw_framebuffer_scaled(
    const uint16_t *pixels,
    int w,
    int h,
    int scale,
    const uint16_t *overlay,
    int overlay_w,
    int overlay_h,
    int overlay_x,
    int overlay_y,
    bool overlay_flip_x,
    uint16_t transparent
);
uint32_t ili9341_spi_baudrate(void);
