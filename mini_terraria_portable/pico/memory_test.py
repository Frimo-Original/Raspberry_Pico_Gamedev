import gc

from backends.pico_backend import PicoInput, PicoRenderer
from game_core import Game


def print_memory(label, frame, base_free):
    gc.collect()
    free = gc.mem_free()
    used_delta = base_free - free
    print(label, "frame:", frame, "free:", free, "delta:", used_delta)
    return free


def main():
    app = Game()
    renderer = PicoRenderer()
    controls = PicoInput()

    gc.collect()
    base_free = gc.mem_free()
    last_free = print_memory("start", 0, base_free)

    frames = 1000
    report_every = 100

    for frame in range(1, frames + 1):
        app.update(controls.poll())
        app.draw(renderer)

        if frame % report_every == 0:
            last_free = print_memory("sample", frame, base_free)

    end_free = print_memory("end", frames, base_free)
    print("stable:", abs(end_free - last_free) < 128)


main()

