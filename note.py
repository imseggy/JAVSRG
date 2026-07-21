# This is just the note settings nothing interesting here :( wish i could make it as cool as you :)

from settings import LANE_COLORS
from utils import draw_smooth_circle


class Note:
    def __init__(self, direction_idx, x, time_ms):
        self.direction_idx = direction_idx
        self.x = x
        self.time_ms = time_ms
        self.y = -100

    def update_position(self, current_time_ms, receptor_y, px_per_ms):
        self.y = receptor_y - (self.time_ms - current_time_ms) * px_per_ms

    def draw(self, surface, lane_width):
        radius = (lane_width - 14) // 2
        center = (self.x, self.y)

        draw_smooth_circle(
            surface,
            LANE_COLORS[self.direction_idx],
            center,
            radius,
            outline_color=(255, 255, 255),
            outline_thickness=2
        )
