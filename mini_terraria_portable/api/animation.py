class Animation:
    def __init__(self, frames, frame_ms=120):
        self.frames = frames
        self.frame_ms = frame_ms

    def frame(self, time_ms):
        if not self.frames:
            return None
        index = (time_ms // self.frame_ms) % len(self.frames)
        return self.frames[index]


class SpriteState:
    IDLE = "idle"
    WALK = "walk"
    JUMP = "jump"
