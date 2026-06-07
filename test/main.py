from api import GameObject, RED, SKY
from backends.tkinter_backend import run

WIDTH = 160
HEIGHT = 120

class MyGame:
    def __init__(self):
        self.player = GameObject(100, 80, 16, 32, RED)

    def update(self, keys):
        pass

    def draw(self, gfx):
        gfx.clear(SKY)
        self.player.draw(gfx)
        gfx.present()

run(MyGame())