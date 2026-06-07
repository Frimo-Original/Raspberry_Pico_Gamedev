# Pico Files

После прошивки кастомного MicroPython с нативным модулем `game` скопируй на
Pico:

```text
api/
game_core/
backends/
```

А файл:

```text
pico/main.py
```

нужно положить в корень Pico как:

```text
main.py
```

Из корня проекта это делает автоматический скрипт:

```bash
python3 tools/upload_to_pico.py
```

Вручную, если установлен `mpremote`:

```bash
mpremote cp -r api :
mpremote cp -r game_core :
mpremote cp -r backends :
mpremote cp pico/main.py :main.py
```

Проверка нативного модуля в REPL:

```python
import game
game.init()
game.clear(game.BLUE)
game.rect(20, 20, 40, 30, game.RED)
game.present()
```

Замер FPS:

```bash
python3 tools/fps_test.py
```

Проверка памяти:

```bash
python3 tools/memory_test.py
```

Текущая распиновка:

```text
ILI9341: CS GP17, RST GP20, DC GP21, MOSI GP19, SCK GP18, MISO GP16, BL 3V3
Joystick: VRX GP26, VRY GP27, SW GP12
D-pad: UP GP13, DOWN GP14, LEFT GP15, RIGHT GP22
```
