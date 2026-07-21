# Just the JSON utilities, pretty cool i say

import os
import json
import pygame
import pygame.gfxdraw
from settings import CHARTS_DIR


def draw_smooth_circle(surface, color, center, radius, outline_color=None, outline_thickness=1):
    """Draws anti-aliased filled and stroked circles using gfxdraw."""
    x, y = int(center[0]), int(center[1])
    r = int(radius)

    pygame.gfxdraw.filled_circle(surface, x, y, r, color)
    pygame.gfxdraw.aacircle(surface, x, y, r, color)

    if outline_color:
        for t in range(outline_thickness):
            pygame.gfxdraw.aacircle(surface, x, y, r - t, outline_color)


def list_json_files():
    if not os.path.exists(CHARTS_DIR):
        os.makedirs(CHARTS_DIR)
    return [os.path.join(CHARTS_DIR, f) for f in os.listdir(CHARTS_DIR) if f.endswith('.json')]


def get_song_title(json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            if 'song' in data and data['song']:
                return os.path.splitext(os.path.basename(data['song']))[0]
            else:
                return os.path.splitext(os.path.basename(json_file))[0]
    except Exception:
        return os.path.splitext(os.path.basename(json_file))[0]


def parse_line(line_raw):
    if isinstance(line_raw, list):
        parts = [str(x) for x in line_raw]
    elif isinstance(line_raw, str):
        parts = line_raw.split()
    else:
        parts = []
    while len(parts) < 4:
        parts.append('.')
    return parts[:4]
