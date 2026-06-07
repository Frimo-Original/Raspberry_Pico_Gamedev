# Native `game` MicroPython Module

Это низкоуровневый модуль для Raspberry Pi Pico + ILI9341.

Он собирается внутрь кастомной прошивки MicroPython и дает Python-модуль:

```python
import game

game.init()
game.clear(0x0000)
game.rect(10, 10, 20, 12, 0xF800)
game.present()
```

Логический экран игры: `160x120`.
Физический экран ILI9341: `320x240`.
Модуль масштабирует координаты в 2 раза.

Отрисовка идет через framebuffer в RAM: `clear()` и `rect()` меняют буфер
160x120, а `present()` отправляет уже готовый кадр на дисплей. Это убирает
видимую перерисовку отдельных прямоугольников.

## Пины

Пины лежат в `game_config.h`. По умолчанию:

```text
SPI0 SCK  GP18
SPI0 MOSI GP19
SPI0 MISO GP16
ILI9341 CS  GP17
ILI9341 RST GP20
ILI9341 DC  GP21
ILI9341 BL  3V3

JOY VRX GP26 / ADC0
JOY VRY GP27 / ADC1
JOY SW  GP12

DPAD UP    GP13
DPAD DOWN  GP14
DPAD LEFT  GP15
DPAD RIGHT GP22
```

Кнопка джойстика и кнопки креста подключаются между GPIO и GND.
Для них включены внутренние pull-up резисторы.

Сейчас управление такое:

- крест влево/вправо - ходьба
- крест вверх - прыжок
- крест вниз - зарезервирован для проваливания через платформу
- VRX/VRY - выбор блока и навигация по верхней панели
- SW - открыть панель или подтвердить выбранный слот
- отдельная физическая кнопка ломания/установки блока пока не назначена

## Сборка MicroPython с модулем

Пример, если MicroPython лежит в `/Users/frimo/PicoSDK/micropython`,
а этот проект в текущей папке:

```bash
cd /Users/frimo/PicoSDK/micropython
make -C mpy-cross
cd ports/rp2
make BOARD=RPI_PICO USER_C_MODULES=/Users/frimo/Documents/Codex/2026-05-28/raspberry-pi-pico-30/mini_terraria_portable/native_game_module
```

Готовая прошивка будет примерно тут:

```text
/Users/frimo/PicoSDK/micropython/ports/rp2/build-RPI_PICO/firmware.uf2
```

Эта сборка уже была проверена для текущего проекта: модуль `game` найден
MicroPython и прошивка успешно линкуется.

После прошивки на Pico можно проверить в REPL:

```python
import game
game.init()
game.clear(game.BLUE)
game.rect(20, 20, 40, 30, game.RED)
game.present()
```
