import game

game.init()
print("spi_baudrate:", game.spi_baudrate())

last = game.ticks_ms()
frames = 0

while True:
    t = game.ticks_ms()
    color = 0x001F if (frames % 2 == 0) else 0x07E0
    game.clear(color)
    game.rect(10 + (frames % 100), 20, 30, 20, 0xF800)
    game.rect(30, 70, 80, 12, 0xFFFF)
    game.present()

    frames += 1
    if game.ticks_ms() - last >= 1000:
        print("fps:", frames, "present_ms:", game.frame_ms(), "max_present_fps:", game.fps())
        frames = 0
        last = game.ticks_ms()
