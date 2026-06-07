# Mini Terraria Portable

Учебный каркас игры, где игровая логика не зависит от библиотеки отрисовки.

Короткое описание учебного API для детей:

```text
docs/STUDENT_API.md
```

Идея:

```text
game_core/       неизменная игровая логика
api/             маленький общий интерфейс: экран, ввод, время, цвета
backends/        заменяемые реализации API
run_tkinter.py   запуск на компьютере
pico/main.py     будущий запуск на Raspberry Pi Pico
```

На компьютере игра запускается через Tkinter:

```bash
cd mini_terraria_portable
python3 run_tkinter.py
```

Или через удобный скрипт для PyCharm:

```bash
python3 tools/run_on_computer.py
```

Запустить маленький пример “поймай подарок”:

```bash
python3 tools/run_catch_gift.py
```

Управление:

- `A` / `Left` - влево
- `D` / `Right` - вправо
- `Space` / `W` / `Up` - прыжок
- левая кнопка мыши - убрать блок
- правая кнопка мыши - поставить блок

На Pico должна меняться только библиотека в `backends/pico_backend.py`.
Логика в `game_core/` остается той же.

Низкоуровневый C++/MicroPython модуль для ILI9341 лежит в
`native_game_module/`.

## Запуск на Pico

На Pico есть две разные части.

Первая часть - прошивка:

```text
MicroPython + native C++ module game + ILI9341 driver
```

Ее надо ставить редко: первый раз или после изменений в `native_game_module/`.

Готовый файл после сборки:

```text
/Users/frimo/PicoSDK/micropython/ports/rp2/build-RPI_PICO/firmware.uf2
```

Вторая часть - Python-файлы игры:

```text
main.py
api/
game_core/
backends/
assets/
```

Их дети обновляют часто. Для этого есть одна команда:

```bash
python3 tools/upload_to_pico.py
```

Если `mpremote` еще не установлен:

```bash
python3 -m pip install mpremote
```

Проверить дисплей и нативный модуль:

```bash
python3 tools/test_display.py
```

Замерить FPS:

```bash
python3 tools/fps_test.py
```

Проверить, не растет ли расход памяти в игровом цикле:

```bash
python3 tools/memory_test.py
```

Редактор спрайтов:

```bash
python3 tools/sprite_editor.py
```

Он сохраняет спрайты в `assets/sprites/`: `.json` для повторного открытия в
редакторе и `.bin` в формате RGB565 для будущей загрузки на Pico.

Принятая модель размеров:

```text
tile           8x8   блок мира
item           8x8   предмет
player_layer   8x16  один слой игрока
player_hires   16x32 hi-res игрок для текущей игры
enemy          8x16  обычный враг
free           любой тестовый спрайт
```

Редактируемый игрок собирается слоями из `assets/sprites/player/`:

```text
skin_default
hair_spiky
eyes_blue
shirt_blue
pants_dark
boots_black
```

Все слои игрока имеют одинаковый размер `8x16` и рисуются в одну позицию.
Прозрачные пиксели `0xF81F` пропускаются, поэтому прическа, глаза, одежда и
ботинки накладываются поверх базового слоя кожи.

Текущая игра уже использует hi-res игрока:

```text
assets/sprites/player_hires/player_default.json
assets/sprites/player_hires/player_default.bin
```

Редактируй его в режиме `player_hires` размером `16x32`. После сохранения
достаточно выполнить `python3 tools/upload_to_pico.py`; прошивать UF2 заново
не нужно, если менялась только картинка.

Можно быстро импортировать PNG в hi-res игрока:

```bash
python3 tools/import_player_image.py /path/to/player.png --name player_default --transparent-top-left
```

Скрипт создаст `assets/sprites/player_hires/player_default.json` и `.bin`.
Если у PNG уже есть прозрачность, флаг `--transparent-top-left` не нужен.

После этого код игры продолжит использовать ту же `game_core`-логику, но
отрисовка пойдет через нативный C++ модуль `game`.

Будущая C++ прошивка MicroPython должна дать модуль `game` примерно с такими
функциями:

```python
game.init()
game.clear(color)
game.rect(x, y, w, h, color)
game.present()
game.btn_left()
game.btn_right()
game.btn_jump()
game.btn_down()
game.btn_menu()
game.action_x()
game.action_y()
game.action_dig()
game.action_place()
game.ticks_ms()
game.sleep_ms(ms)
```
