#include "py/obj.h"
#include "py/runtime.h"

#include "engine_c.h"

static mp_obj_t game_init(void) {
    engine_init();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_init_obj, game_init);

static mp_obj_t game_clear(mp_obj_t color_obj) {
    engine_clear((uint16_t)mp_obj_get_int(color_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(game_clear_obj, game_clear);

static mp_obj_t game_rect(size_t n_args, const mp_obj_t *args) {
    engine_rect(
        mp_obj_get_int(args[0]),
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),
        mp_obj_get_int(args[3]),
        (uint16_t)mp_obj_get_int(args[4])
    );
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(game_rect_obj, 5, 5, game_rect);

static mp_obj_t game_tile(size_t n_args, const mp_obj_t *args) {
    engine_tile(
        mp_obj_get_int(args[0]),
        mp_obj_get_int(args[1]),
        (uint16_t)mp_obj_get_int(args[2]),
        (uint16_t)mp_obj_get_int(args[3])
    );
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(game_tile_obj, 4, 4, game_tile);

static mp_obj_t game_load_tile_sprite(mp_obj_t tile_id_obj, mp_obj_t data_obj) {
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(data_obj, &bufinfo, MP_BUFFER_READ);
    if (!engine_load_tile_sprite(mp_obj_get_int(tile_id_obj), (const uint8_t *)bufinfo.buf, (uint32_t)bufinfo.len)) {
        mp_raise_ValueError(MP_ERROR_TEXT("tile sprite must be 8x8 RGB565_BE"));
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(game_load_tile_sprite_obj, game_load_tile_sprite);

static mp_obj_t game_tile_sprite(size_t n_args, const mp_obj_t *args) {
    engine_tile_sprite(
        mp_obj_get_int(args[0]),
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2])
    );
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(game_tile_sprite_obj, 3, 3, game_tile_sprite);

static mp_obj_t game_image(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(args[4], &bufinfo, MP_BUFFER_READ);
    if (!engine_image(
        mp_obj_get_int(args[0]),
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),
        mp_obj_get_int(args[3]),
        (const uint8_t *)bufinfo.buf,
        (uint32_t)bufinfo.len
    )) {
        mp_raise_ValueError(MP_ERROR_TEXT("image data size must be width*height*2 RGB565_BE"));
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(game_image_obj, 5, 5, game_image);

static mp_obj_t game_load_player_sprite(mp_obj_t data_obj) {
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(data_obj, &bufinfo, MP_BUFFER_READ);
    if (!engine_load_player_sprite((const uint8_t *)bufinfo.buf, (uint32_t)bufinfo.len)) {
        mp_raise_ValueError(MP_ERROR_TEXT("player sprite must be 16x32 RGB565_BE"));
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(game_load_player_sprite_obj, game_load_player_sprite);

static mp_obj_t game_player(size_t n_args, const mp_obj_t *args) {
    engine_player(
        mp_obj_get_int(args[0]),
        mp_obj_get_int(args[1]),
        n_args >= 3 && mp_obj_is_true(args[2])
    );
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(game_player_obj, 2, 3, game_player);

static mp_obj_t game_present(void) {
    engine_present();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_present_obj, game_present);

static mp_obj_t game_btn_left(void) {
    return mp_obj_new_bool(engine_btn_left());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_btn_left_obj, game_btn_left);

static mp_obj_t game_btn_right(void) {
    return mp_obj_new_bool(engine_btn_right());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_btn_right_obj, game_btn_right);

static mp_obj_t game_btn_jump(void) {
    return mp_obj_new_bool(engine_btn_jump());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_btn_jump_obj, game_btn_jump);

static mp_obj_t game_btn_down(void) {
    return mp_obj_new_bool(engine_btn_down());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_btn_down_obj, game_btn_down);

static mp_obj_t game_btn_menu(void) {
    return mp_obj_new_bool(engine_btn_menu());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_btn_menu_obj, game_btn_menu);

static mp_obj_t game_action_x(void) {
    return mp_obj_new_int(engine_action_x());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_action_x_obj, game_action_x);

static mp_obj_t game_action_y(void) {
    return mp_obj_new_int(engine_action_y());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_action_y_obj, game_action_y);

static mp_obj_t game_action_dig(void) {
    return mp_obj_new_bool(engine_action_dig());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_action_dig_obj, game_action_dig);

static mp_obj_t game_action_place(void) {
    return mp_obj_new_bool(engine_action_place());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_action_place_obj, game_action_place);

static mp_obj_t game_ticks_ms(void) {
    return mp_obj_new_int_from_uint(engine_ticks_ms());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_ticks_ms_obj, game_ticks_ms);

static mp_obj_t game_sleep_ms(mp_obj_t ms_obj) {
    engine_sleep_ms((uint32_t)mp_obj_get_int(ms_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(game_sleep_ms_obj, game_sleep_ms);

static mp_obj_t game_frame_ms(void) {
    return mp_obj_new_int_from_uint(engine_frame_ms());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_frame_ms_obj, game_frame_ms);

static mp_obj_t game_fps(void) {
    return mp_obj_new_int_from_uint(engine_fps());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_fps_obj, game_fps);

static mp_obj_t game_spi_baudrate(void) {
    return mp_obj_new_int_from_uint(engine_spi_baudrate());
}
static MP_DEFINE_CONST_FUN_OBJ_0(game_spi_baudrate_obj, game_spi_baudrate);

static const mp_rom_map_elem_t game_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_game) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&game_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_clear), MP_ROM_PTR(&game_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_rect), MP_ROM_PTR(&game_rect_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile), MP_ROM_PTR(&game_tile_obj) },
    { MP_ROM_QSTR(MP_QSTR_load_tile_sprite), MP_ROM_PTR(&game_load_tile_sprite_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_sprite), MP_ROM_PTR(&game_tile_sprite_obj) },
    { MP_ROM_QSTR(MP_QSTR_image), MP_ROM_PTR(&game_image_obj) },
    { MP_ROM_QSTR(MP_QSTR_load_player_sprite), MP_ROM_PTR(&game_load_player_sprite_obj) },
    { MP_ROM_QSTR(MP_QSTR_player), MP_ROM_PTR(&game_player_obj) },
    { MP_ROM_QSTR(MP_QSTR_present), MP_ROM_PTR(&game_present_obj) },
    { MP_ROM_QSTR(MP_QSTR_btn_left), MP_ROM_PTR(&game_btn_left_obj) },
    { MP_ROM_QSTR(MP_QSTR_btn_right), MP_ROM_PTR(&game_btn_right_obj) },
    { MP_ROM_QSTR(MP_QSTR_btn_jump), MP_ROM_PTR(&game_btn_jump_obj) },
    { MP_ROM_QSTR(MP_QSTR_btn_down), MP_ROM_PTR(&game_btn_down_obj) },
    { MP_ROM_QSTR(MP_QSTR_btn_menu), MP_ROM_PTR(&game_btn_menu_obj) },
    { MP_ROM_QSTR(MP_QSTR_action_x), MP_ROM_PTR(&game_action_x_obj) },
    { MP_ROM_QSTR(MP_QSTR_action_y), MP_ROM_PTR(&game_action_y_obj) },
    { MP_ROM_QSTR(MP_QSTR_action_dig), MP_ROM_PTR(&game_action_dig_obj) },
    { MP_ROM_QSTR(MP_QSTR_action_place), MP_ROM_PTR(&game_action_place_obj) },
    { MP_ROM_QSTR(MP_QSTR_ticks_ms), MP_ROM_PTR(&game_ticks_ms_obj) },
    { MP_ROM_QSTR(MP_QSTR_sleep_ms), MP_ROM_PTR(&game_sleep_ms_obj) },
    { MP_ROM_QSTR(MP_QSTR_frame_ms), MP_ROM_PTR(&game_frame_ms_obj) },
    { MP_ROM_QSTR(MP_QSTR_fps), MP_ROM_PTR(&game_fps_obj) },
    { MP_ROM_QSTR(MP_QSTR_spi_baudrate), MP_ROM_PTR(&game_spi_baudrate_obj) },
    { MP_ROM_QSTR(MP_QSTR_BLACK), MP_ROM_INT(0x0000) },
    { MP_ROM_QSTR(MP_QSTR_RED), MP_ROM_INT(0xF800) },
    { MP_ROM_QSTR(MP_QSTR_GREEN), MP_ROM_INT(0x07E0) },
    { MP_ROM_QSTR(MP_QSTR_BLUE), MP_ROM_INT(0x001F) },
    { MP_ROM_QSTR(MP_QSTR_WHITE), MP_ROM_INT(0xFFFF) },
};
static MP_DEFINE_CONST_DICT(game_module_globals, game_module_globals_table);

const mp_obj_module_t game_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&game_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_game, game_user_cmodule);
