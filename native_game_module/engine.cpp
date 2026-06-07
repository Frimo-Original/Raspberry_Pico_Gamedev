#include "engine_c.h"

#include "game_config.h"
#include "ili9341.hpp"

#include "hardware/adc.h"
#include "hardware/gpio.h"
#include "pico/stdlib.h"

namespace {

bool initialized = false;
uint16_t framebuffer[GAME_SCREEN_W * GAME_SCREEN_H];
constexpr int sprite8_count = 32;
uint16_t tile_sprites[sprite8_count][8 * 8];
bool tile_sprite_loaded[sprite8_count] = {};
uint16_t player_sprite[16 * 32];
bool player_visible = false;
int player_x = 0;
int player_y = 0;
bool player_flip_x = false;
uint32_t last_present_ms = 0;
uint32_t last_frame_ms = 0;
uint32_t last_fps = 0;

constexpr uint16_t T = 0xF81F;
constexpr uint16_t K = 0x0000;
constexpr uint16_t S = 0xFDB8;
constexpr uint16_t H = 0x4208;
constexpr uint16_t E = 0x001F;
constexpr uint16_t M = 0x6378;
constexpr uint16_t R = 0x3D9F;
constexpr uint16_t P = 0x18E3;
constexpr uint16_t B = 0x0000;

const char *player_art[32] = {
    "TTTTTHHHHHHTTTTT",
    "TTTTHHHHHHHHTTTT",
    "TTTHHHHHHHHHHTTT",
    "TTHHHHHHHHHHHHTT",
    "TTHHHSSSSSSHHHTT",
    "TTHHSSSSSSSSHHHT",
    "TTHHSESSSSESHHTT",
    "TTHHSSSSSSSSHTTT",
    "TTTHSSSMMSSHTTTT",
    "TTTTHSSSSSHTTTTT",
    "TTTTTSSSSSTTTTTT",
    "TTTRRRRRRRRRTTTT",
    "TTRRRRRRRRRRRTTT",
    "TTRRSSRRRRSSRTTT",
    "TTRRSSRRRRSSRTTT",
    "TTTRRRRRRRRTTTTT",
    "TTTTRRRRRRTTTTTT",
    "TTTTTPPPPTTTTTTT",
    "TTTTTPPPPTTTTTTT",
    "TTTTTPPPPTTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTTPPTTPPTTTTTT",
    "TTTBBTTTTBBTTTTT",
    "TTBBBBTTBBBBTTTT",
    "TTBBBBTTBBBBTTTT",
    "TTTBBTTTTBBTTTTT",
};

bool switch_pressed(uint pin) {
    return gpio_get(pin) == 0;
}

void init_switch(uint pin) {
    gpio_init(pin);
    gpio_set_dir(pin, GPIO_IN);
    gpio_pull_up(pin);
}

uint16_t read_adc(uint input) {
    adc_select_input(input);
    return adc_read();
}

uint16_t color_for(char value) {
    switch (value) {
        case 'K': return K;
        case 'S': return S;
        case 'H': return H;
        case 'E': return E;
        case 'M': return M;
        case 'R': return R;
        case 'P': return P;
        case 'B': return B;
        default: return T;
    }
}

void init_player_sprite() {
    for (int y = 0; y < 32; ++y) {
        for (int x = 0; x < 16; ++x) {
            player_sprite[y * 16 + x] = color_for(player_art[y][x]);
        }
    }
}

}

extern "C" void engine_init(void) {
    if (initialized) {
        return;
    }

    stdio_init_all();
    adc_init();
    adc_gpio_init(GAME_PIN_JOY_X);
    adc_gpio_init(GAME_PIN_JOY_Y);
    init_switch(GAME_PIN_JOY_SW);
    init_switch(GAME_PIN_DPAD_DOWN);
    init_switch(GAME_PIN_DPAD_UP);
    init_switch(GAME_PIN_DPAD_LEFT);
    init_switch(GAME_PIN_DPAD_RIGHT);

    init_player_sprite();
    ili9341_init();
    initialized = true;
}

extern "C" void engine_clear(uint16_t color) {
    engine_init();
    player_visible = false;
    for (int i = 0; i < GAME_SCREEN_W * GAME_SCREEN_H; ++i) {
        framebuffer[i] = color;
    }
}

extern "C" void engine_rect(int x, int y, int w, int h, uint16_t color) {
    engine_init();
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

    for (int row = 0; row < h; ++row) {
        uint16_t *dst = framebuffer + (y + row) * GAME_SCREEN_W + x;
        for (int col = 0; col < w; ++col) {
            dst[col] = color;
        }
    }
}

extern "C" void engine_tile(int x, int y, uint16_t color, uint16_t top_color) {
    engine_init();

    constexpr int tile = 8;
    for (int row = 0; row < tile; ++row) {
        int py = y + row;
        if (py < 0 || py >= GAME_SCREEN_H) {
            continue;
        }

        uint16_t draw_color = row == 0 ? top_color : color;
        for (int col = 0; col < tile; ++col) {
            int px = x + col;
            if (px >= 0 && px < GAME_SCREEN_W) {
                framebuffer[py * GAME_SCREEN_W + px] = draw_color;
            }
        }
    }
}

extern "C" bool engine_load_tile_sprite(int tile_id, const uint8_t *data, uint32_t len) {
    engine_init();
    constexpr uint32_t expected = 8 * 8 * 2;
    if (tile_id < 0 || tile_id >= sprite8_count || data == nullptr || len != expected) {
        return false;
    }

    for (uint32_t i = 0; i < 8 * 8; ++i) {
        tile_sprites[tile_id][i] = (static_cast<uint16_t>(data[i * 2]) << 8) | data[i * 2 + 1];
    }
    tile_sprite_loaded[tile_id] = true;
    return true;
}

extern "C" void engine_tile_sprite(int x, int y, int tile_id) {
    engine_init();
    if (tile_id < 0 || tile_id >= sprite8_count || !tile_sprite_loaded[tile_id]) {
        return;
    }

    constexpr int tile = 8;
    const uint16_t *sprite = tile_sprites[tile_id];
    for (int row = 0; row < tile; ++row) {
        int py = y + row;
        if (py < 0 || py >= GAME_SCREEN_H) {
            continue;
        }

        for (int col = 0; col < tile; ++col) {
            int px = x + col;
            if (px < 0 || px >= GAME_SCREEN_W) {
                continue;
            }
            uint16_t color = sprite[row * tile + col];
            if (color != T) {
                framebuffer[py * GAME_SCREEN_W + px] = color;
            }
        }
    }
}

extern "C" bool engine_image(int x, int y, int w, int h, const uint8_t *data, uint32_t len) {
    engine_init();
    if (w <= 0 || h <= 0 || data == nullptr || len != static_cast<uint32_t>(w * h * 2)) {
        return false;
    }

    for (int row = 0; row < h; ++row) {
        int py = y + row;
        if (py < 0 || py >= GAME_SCREEN_H) {
            continue;
        }
        for (int col = 0; col < w; ++col) {
            int px = x + col;
            if (px < 0 || px >= GAME_SCREEN_W) {
                continue;
            }
            uint32_t i = static_cast<uint32_t>((row * w + col) * 2);
            uint16_t color = (static_cast<uint16_t>(data[i]) << 8) | data[i + 1];
            if (color != T) {
                framebuffer[py * GAME_SCREEN_W + px] = color;
            }
        }
    }
    return true;
}

extern "C" bool engine_load_player_sprite(const uint8_t *data, uint32_t len) {
    engine_init();
    constexpr uint32_t expected = 16 * 32 * 2;
    if (data == nullptr || len != expected) {
        return false;
    }

    for (uint32_t i = 0; i < 16 * 32; ++i) {
        player_sprite[i] = (static_cast<uint16_t>(data[i * 2]) << 8) | data[i * 2 + 1];
    }
    return true;
}

extern "C" void engine_player(int x, int y, bool flip_x) {
    engine_init();
    player_visible = true;
    player_x = x * GAME_DISPLAY_SCALE - 1;
    player_y = y * GAME_DISPLAY_SCALE;
    player_flip_x = flip_x;
}

extern "C" void engine_present(void) {
    engine_init();
    uint32_t start = to_ms_since_boot(get_absolute_time());
    ili9341_draw_framebuffer_scaled(
        framebuffer,
        GAME_SCREEN_W,
        GAME_SCREEN_H,
        GAME_DISPLAY_SCALE,
        player_visible ? player_sprite : nullptr,
        16,
        32,
        player_x,
        player_y,
        player_flip_x,
        T
    );
    uint32_t end = to_ms_since_boot(get_absolute_time());
    last_present_ms = end - start;
    if (last_present_ms > 0) {
        last_fps = 1000 / last_present_ms;
    } else {
        last_fps = 0;
    }
    last_frame_ms = last_present_ms;
}

extern "C" bool engine_btn_left(void) {
    return switch_pressed(GAME_PIN_DPAD_LEFT);
}

extern "C" bool engine_btn_right(void) {
    return switch_pressed(GAME_PIN_DPAD_RIGHT);
}

extern "C" bool engine_btn_jump(void) {
    return switch_pressed(GAME_PIN_DPAD_UP);
}

extern "C" bool engine_btn_down(void) {
    return switch_pressed(GAME_PIN_DPAD_DOWN);
}

extern "C" bool engine_btn_menu(void) {
    return switch_pressed(GAME_PIN_JOY_SW);
}

extern "C" int engine_action_x(void) {
    uint16_t raw = read_adc(GAME_JOY_ADC_X);
    int x = static_cast<int>(raw) * GAME_SCREEN_W / 4095;
    if (x < 0) {
        x = 0;
    }
    if (x >= GAME_SCREEN_W) {
        x = GAME_SCREEN_W - 1;
    }
    return x;
}

extern "C" int engine_action_y(void) {
    uint16_t raw = read_adc(GAME_JOY_ADC_Y);
    int y = static_cast<int>(raw) * GAME_SCREEN_H / 4095;
    if (y < 0) {
        y = 0;
    }
    if (y >= GAME_SCREEN_H) {
        y = GAME_SCREEN_H - 1;
    }
    return y;
}

extern "C" bool engine_action_dig(void) {
    return false;
}

extern "C" bool engine_action_place(void) {
    return false;
}

extern "C" uint32_t engine_ticks_ms(void) {
    return to_ms_since_boot(get_absolute_time());
}

extern "C" void engine_sleep_ms(uint32_t ms) {
    sleep_ms(ms);
}

extern "C" uint32_t engine_frame_ms(void) {
    return last_frame_ms;
}

extern "C" uint32_t engine_fps(void) {
    return last_fps;
}

extern "C" uint32_t engine_spi_baudrate(void) {
    engine_init();
    return ili9341_spi_baudrate();
}
