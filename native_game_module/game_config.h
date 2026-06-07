#pragma once

#define GAME_SCREEN_W 160
#define GAME_SCREEN_H 120
#define GAME_DISPLAY_SCALE 2

#define ILI9341_SPI_PORT spi0
#define ILI9341_SPI_BAUD 62500000

#define ILI9341_PIN_SCK 18
#define ILI9341_PIN_MOSI 19
#define ILI9341_PIN_MISO 16
#define ILI9341_PIN_CS 17
#define ILI9341_PIN_RST 20
#define ILI9341_PIN_DC 21

// Set to -1 when LED/BL is connected directly to 3V3.
#define ILI9341_PIN_BL -1

// Landscape 320x240. Use 0xE8 if the image is rotated the wrong way.
#define ILI9341_MADCTL 0x28

#define GAME_PIN_JOY_X 26
#define GAME_PIN_JOY_Y 27
#define GAME_PIN_JOY_SW 12

#define GAME_PIN_DPAD_UP 13
#define GAME_PIN_DPAD_DOWN 14
#define GAME_PIN_DPAD_LEFT 15
#define GAME_PIN_DPAD_RIGHT 22

#define GAME_JOY_ADC_X 0
#define GAME_JOY_ADC_Y 1
#define GAME_JOY_LOW 1500
#define GAME_JOY_HIGH 2600
