import os
import json
import pygame

FPS = 60
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FONT_STACK = "ubuntu,aller,cantarell,dejavusans,sans-serif"

HEALTH_MAX = 100
HIT_WINDOWS = {
    'sick': 30,
    'good': 60,
    'bad': 100,
    'trash': 130
}

DIRECTIONS = ['left', 'down', 'up', 'right']
LANE_COLORS = [(192, 57, 43), (41, 128, 185), (39, 174, 96), (241, 196, 15)]
LANE_HIGHLIGHT_COLORS = [(240, 90, 75), (80, 180, 240), (75, 230, 140), (255, 225, 80)]

CHARTS_DIR = "charts"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "key_mapping": {
        "left": pygame.K_a,
        "down": pygame.K_s,
        "up": pygame.K_k,
        "right": pygame.K_l
    },
    "volume": 0.8,
    "scroll_speed": 0.7,
    "offset_ms": 0
}

def load_settings():
    """Loads configuration settings from JSON or defaults if absent/corrupt."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return {
                    "key_mapping": {
                        "left": data.get("key_mapping", {}).get("left", pygame.K_a),
                        "down": data.get("key_mapping", {}).get("down", pygame.K_s),
                        "up": data.get("key_mapping", {}).get("up", pygame.K_k),
                        "right": data.get("key_mapping", {}).get("right", pygame.K_l)
                    },
                    "volume": data.get("volume", 0.8),
                    "scroll_speed": data.get("scroll_speed", 0.7),
                    "offset_ms": data.get("offset_ms", 0)
                }
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_SETTINGS))


def save_settings(settings):
    """Saves user configuration settings locally."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Failed to save settings: {e}")
