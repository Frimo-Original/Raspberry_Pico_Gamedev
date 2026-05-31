class Keys:
    def __init__(self):
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.button_a = False
        self.button_b = False
        self.button_menu = False
        self.pointer_x = 0
        self.pointer_y = 0
        self.pointer_active = False
        self.axis_x = 0
        self.axis_y = 0

    @property
    def any_button(self):
        return self.button_a or self.button_b or self.button_menu
