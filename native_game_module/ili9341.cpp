#include "ili9341.hpp"

#include "game_config.h"

#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/spi.h"
#include "pico/stdlib.h"

#include <cstddef>

namespace {

constexpr uint8_t CMD_SWRESET = 0x01;
constexpr uint8_t CMD_SLPOUT = 0x11;
constexpr uint8_t CMD_DISPON = 0x29;
constexpr uint8_t CMD_CASET = 0x2A;
constexpr uint8_t CMD_PASET = 0x2B;
constexpr uint8_t CMD_RAMWR = 0x2C;
constexpr uint8_t CMD_MADCTL = 0x36;
constexpr uint8_t CMD_PIXFMT = 0x3A;

void cs_select() {
    gpio_put(ILI9341_PIN_CS, 0);
}

void cs_deselect() {
    gpio_put(ILI9341_PIN_CS, 1);
}

void dc_command() {
    gpio_put(ILI9341_PIN_DC, 0);
}

void dc_data() {
    gpio_put(ILI9341_PIN_DC, 1);
}

void write_bytes(const uint8_t *data, size_t len) {
    spi_write_blocking(ILI9341_SPI_PORT, data, len);
}

void set_spi_8bit(void) {
    spi_set_format(ILI9341_SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
}

void set_spi_16bit(void) {
    spi_set_format(ILI9341_SPI_PORT, 16, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
}

void write_cmd(uint8_t cmd) {
    dc_command();
    cs_select();
    write_bytes(&cmd, 1);
    cs_deselect();
}

void write_data(const uint8_t *data, size_t len) {
    dc_data();
    cs_select();
    write_bytes(data, len);
    cs_deselect();
}

void write_data8(uint8_t value) {
    write_data(&value, 1);
}

void set_addr_window(int x0, int y0, int x1, int y1) {
    uint8_t data[4];

    write_cmd(CMD_CASET);
    data[0] = static_cast<uint8_t>(x0 >> 8);
    data[1] = static_cast<uint8_t>(x0);
    data[2] = static_cast<uint8_t>(x1 >> 8);
    data[3] = static_cast<uint8_t>(x1);
    write_data(data, 4);

    write_cmd(CMD_PASET);
    data[0] = static_cast<uint8_t>(y0 >> 8);
    data[1] = static_cast<uint8_t>(y0);
    data[2] = static_cast<uint8_t>(y1 >> 8);
    data[3] = static_cast<uint8_t>(y1);
    write_data(data, 4);

    write_cmd(CMD_RAMWR);
}

void push_color(uint16_t color, int pixels) {
    uint8_t hi = static_cast<uint8_t>(color >> 8);
    uint8_t lo = static_cast<uint8_t>(color);
    uint8_t buffer[128];

    for (size_t i = 0; i < sizeof(buffer); i += 2) {
        buffer[i] = hi;
        buffer[i + 1] = lo;
    }

    dc_data();
    cs_select();
    int remaining = pixels * 2;
    while (remaining > 0) {
        int chunk = remaining;
        if (chunk > static_cast<int>(sizeof(buffer))) {
            chunk = sizeof(buffer);
        }
        write_bytes(buffer, chunk);
        remaining -= chunk;
    }
    cs_deselect();
}

}

void ili9341_init(void) {
    uint32_t sys_hz = clock_get_hz(clk_sys);
    clock_configure(
        clk_peri,
        0,
        CLOCKS_CLK_PERI_CTRL_AUXSRC_VALUE_CLK_SYS,
        sys_hz,
        sys_hz
    );

    spi_init(ILI9341_SPI_PORT, ILI9341_SPI_BAUD);
    set_spi_8bit();
    gpio_set_function(ILI9341_PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(ILI9341_PIN_MOSI, GPIO_FUNC_SPI);
    gpio_set_function(ILI9341_PIN_MISO, GPIO_FUNC_SPI);

    gpio_init(ILI9341_PIN_CS);
    gpio_set_dir(ILI9341_PIN_CS, GPIO_OUT);
    gpio_put(ILI9341_PIN_CS, 1);

    gpio_init(ILI9341_PIN_DC);
    gpio_set_dir(ILI9341_PIN_DC, GPIO_OUT);

    gpio_init(ILI9341_PIN_RST);
    gpio_set_dir(ILI9341_PIN_RST, GPIO_OUT);

    if (ILI9341_PIN_BL >= 0) {
        gpio_init(ILI9341_PIN_BL);
        gpio_set_dir(ILI9341_PIN_BL, GPIO_OUT);
        gpio_put(ILI9341_PIN_BL, 1);
    }

    gpio_put(ILI9341_PIN_RST, 0);
    sleep_ms(20);
    gpio_put(ILI9341_PIN_RST, 1);
    sleep_ms(150);

    write_cmd(CMD_SWRESET);
    sleep_ms(150);
    write_cmd(CMD_SLPOUT);
    sleep_ms(150);

    write_cmd(CMD_PIXFMT);
    write_data8(0x55);

    write_cmd(CMD_MADCTL);
    write_data8(ILI9341_MADCTL);

    write_cmd(CMD_DISPON);
    sleep_ms(100);
}

void ili9341_fill_rect(int x, int y, int w, int h, uint16_t color) {
    if (w <= 0 || h <= 0) {
        return;
    }

    if (x < 0) {
        w += x;
        x = 0;
    }
    if (y < 0) {
        h += y;
        y = 0;
    }
    if (x + w > GAME_SCREEN_W) {
        w = GAME_SCREEN_W - x;
    }
    if (y + h > GAME_SCREEN_H) {
        h = GAME_SCREEN_H - y;
    }
    if (w <= 0 || h <= 0) {
        return;
    }

    int sx = x * GAME_DISPLAY_SCALE;
    int sy = y * GAME_DISPLAY_SCALE;
    int sw = w * GAME_DISPLAY_SCALE;
    int sh = h * GAME_DISPLAY_SCALE;

    set_addr_window(sx, sy, sx + sw - 1, sy + sh - 1);
    push_color(color, sw * sh);
}

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
) {
    if (pixels == nullptr || w <= 0 || h <= 0 || scale <= 0) {
        return;
    }

    int out_w = w * scale;
    int out_h = h * scale;
    set_addr_window(0, 0, out_w - 1, out_h - 1);

    uint16_t row[GAME_SCREEN_W * GAME_DISPLAY_SCALE];
    dc_data();
    cs_select();
    set_spi_16bit();

    for (int y = 0; y < h; ++y) {
        uint16_t *dst = row;
        const uint16_t *src = pixels + y * w;

        for (int x = 0; x < w; ++x) {
            uint16_t color = src[x];
            for (int sx = 0; sx < scale; ++sx) {
                *dst++ = color;
            }
        }

        for (int sy = 0; sy < scale; ++sy) {
            int physical_y = y * scale + sy;
            if (overlay != nullptr && physical_y >= overlay_y && physical_y < overlay_y + overlay_h) {
                int overlay_row = physical_y - overlay_y;
                for (int ox = 0; ox < overlay_w; ++ox) {
                    int physical_x = overlay_x + ox;
                    if (physical_x < 0 || physical_x >= out_w) {
                        continue;
                    }
                    int src_x = overlay_flip_x ? overlay_w - 1 - ox : ox;
                    uint16_t color = overlay[overlay_row * overlay_w + src_x];
                    if (color != transparent) {
                        row[physical_x] = color;
                    }
                }
            }
            spi_write16_blocking(ILI9341_SPI_PORT, row, out_w);
        }
    }

    set_spi_8bit();
    cs_deselect();
}

uint32_t ili9341_spi_baudrate(void) {
    return spi_get_baudrate(ILI9341_SPI_PORT);
}
