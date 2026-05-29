class Keys:
    def __init__(self):
        self.left = False
        self.right = False
        self.jump = False
        self.dig = False
        self.place = False
        self.cursor_x = 0
        self.cursor_y = 0
        self.cursor_active = False
        self.aim_x = 0
        self.aim_y = 0
        self.hotbar_toggle = False

    @property
    def action(self):
        return self.jump or self.dig or self.place
