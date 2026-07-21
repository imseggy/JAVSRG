# One of my greatest works ever, not as great as you :D

import pygame
import pygame.gfxdraw
import sys
import os
import json

FPS = 60
DIRECTIONS = ['left', 'down', 'up', 'right']
LANE_COLORS = [(192, 57, 43), (41, 128, 185), (39, 174, 96), (241, 196, 15)]

CHARTS_DIR = "charts"
SONGS_DIR = "songs"
SETTINGS_FILE = "settings.json"
AUDIO_EXTS = ('.mp3', '.wav', '.ogg')

def draw_smooth_circle(surface, color, center, radius, outline_color=None, outline_thickness=1):
    x, y = int(center[0]), int(center[1])
    r = int(radius)

    pygame.gfxdraw.filled_circle(surface, x, y, r, color)
    pygame.gfxdraw.aacircle(surface, x, y, r, color)

    if outline_color:
        for t in range(outline_thickness):
            if r - t > 0:
                pygame.gfxdraw.aacircle(surface, x, y, r - t, outline_color)

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

class Editor:
    def __init__(self, screen):
        self.screen = screen

        FONT_STACK = "ubuntu,aller,cantarell,dejavusans,sans-serif"
        self.font = pygame.font.SysFont(FONT_STACK, 20, bold=True)
        self.big_font = pygame.font.SysFont(FONT_STACK, 32, bold=True)

        self.lane_width = 92
        self.rec_radius = (self.lane_width - 14) // 2

        self.scroll_speed = 0.45
        self.load_settings()

        self.filename = "new_chart.json"
        self.song_path = ""
        self.bpm = 120.0

        self.current_time_ms = 0.0
        self.notes_dict = {}
        self.snap_divisions = [4, 8, 16, 32]
        self.snap_idx = 0

        self.is_playing = False
        self.play_start_time_ms = 0.0
        self.last_ticks = pygame.time.get_ticks()

        self.selecting_chart = False
        self.available_charts = []
        self.selector_idx = 0

        self.selecting_song = False
        self.available_songs = []
        self.song_selector_idx = 0
        self.pending_chart_name = ""
        self.pending_bpm = 120.0

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    self.scroll_speed = float(data.get('scroll_speed', 0.45))
            except Exception as e:
                print(f"[SETTINGS] Failed to load settings: {e}")

    def save_settings(self):
        data = {'scroll_speed': round(self.scroll_speed, 2)}
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[SETTINGS] Failed to save settings: {e}")

    def get_beat_ms(self):
        return 60000.0 / self.bpm

    def get_snap_ms(self):
        return self.get_beat_ms() / (self.snap_divisions[self.snap_idx] / 4.0)

    def refresh_chart_list(self):
        if not os.path.exists(CHARTS_DIR):
            os.makedirs(CHARTS_DIR, exist_ok=True)
        self.available_charts = [f for f in os.listdir(CHARTS_DIR) if f.endswith('.json')]
        self.selector_idx = max(0, min(self.selector_idx, len(self.available_charts) - 1))

    def refresh_song_list(self):
        songs = []

        for f in os.listdir('.'):
            if f.lower().endswith(AUDIO_EXTS) and os.path.isfile(f):
                songs.append(f)

        if os.path.exists(SONGS_DIR):
            for f in os.listdir(SONGS_DIR):
                if f.lower().endswith(AUDIO_EXTS):
                    songs.append(os.path.join(SONGS_DIR, f))

        self.available_songs = sorted(songs)
        self.song_selector_idx = max(0, min(self.song_selector_idx, len(self.available_songs) - 1))

    def start_new_chart_flow(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        pygame.event.pump()

        print("\n" + "="*40)
        print(" CREATE NEW CHART")
        print("="*40)
        chart_name = input("Enter Chart Name (e.g. 'my_song'): ").strip()
        if not chart_name:
            chart_name = "new_chart"
        if not chart_name.endswith('.json'):
            chart_name += '.json'

        bpm_str = input("Enter BPM (default 120): ").strip()
        try:
            bpm_val = float(bpm_str) if bpm_str else 120.0
        except ValueError:
            bpm_val = 120.0

        self.pending_chart_name = chart_name
        self.pending_bpm = bpm_val

        self.refresh_song_list()
        if self.available_songs:
            self.selecting_chart = False
            self.selecting_song = True
        else:
            print("[WARN] No audio files (.mp3/.wav/.ogg) found. Proceeding with no song.")
            self.finalize_new_chart("")

    def finalize_new_chart(self, chosen_song_path):
        self.filename = os.path.join(CHARTS_DIR, self.pending_chart_name)
        self.song_path = chosen_song_path
        self.bpm = self.pending_bpm
        self.notes_dict.clear()
        self.current_time_ms = 0.0

        self.save_chart()
        self.load_chart(self.filename)
        self.selecting_song = False
        self.selecting_chart = False
        print(f"[SUCCESS] Created & Loaded '{self.pending_chart_name}' with song '{chosen_song_path}'!\n")

    def load_chart(self, filepath):
        if not os.path.exists(filepath):
            return

        self.filename = filepath
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.song_path = data.get('song', '')
        self.bpm = float(data.get('bpm', 120.0))

        sheet = data.get('musicSheet', [])
        self.notes_dict.clear()

        beat_interval = self.get_beat_ms()
        for i, item in enumerate(sheet):
            if isinstance(item, dict):
                t = float(item.get('time', int(i * beat_interval)))
                line = parse_line(item.get('line', item.get('notes', '')))
            else:
                t = float(i * beat_interval)
                line = parse_line(item)

            if any(c in ['o', '1'] for c in line):
                self.notes_dict[int(round(t))] = line

        if self.song_path and os.path.isfile(self.song_path):
            try:
                pygame.mixer.music.load(self.song_path)
            except Exception as e:
                print(f"[AUDIO ERROR] Failed to load audio: {e}")

    def save_chart(self):
        if not os.path.exists(CHARTS_DIR):
            os.makedirs(CHARTS_DIR, exist_ok=True)

        base_name = os.path.basename(self.filename)
        filepath = os.path.join(CHARTS_DIR, base_name)

        sorted_times = sorted(self.notes_dict.keys())
        music_sheet = []
        for t in sorted_times:
            music_sheet.append({
                "time": int(t),
                "line": self.notes_dict[t]
            })

        data = {
            "song": self.song_path,
            "bpm": self.bpm,
            "scrollSpeed": round(self.scroll_speed, 3),
            "musicSheet": music_sheet
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            self.filename = filepath
            print(f"[SUCCESS] Chart saved to {os.path.abspath(filepath)}")
        except Exception as e:
            print(f"[ERROR] Failed to save chart: {e}")

    def toggle_note_at_time(self, target_time_ms, lane_idx):
        snap_ms = self.get_snap_ms()
        snapped_time = int(round(round(target_time_ms / snap_ms) * snap_ms))

        if snapped_time not in self.notes_dict:
            self.notes_dict[snapped_time] = ['.', '.', '.', '.']

        line = self.notes_dict[snapped_time]
        line[lane_idx] = 'o' if line[lane_idx] == '.' else '.'

        if all(c == '.' for c in line):
            del self.notes_dict[snapped_time]

    def handle_click(self, mouse_pos):
        mx, my = mouse_pos
        screen_w, screen_h = self.screen.get_size()
        receptor_y = int(screen_h * 0.83)
        grid_x_start = (screen_w - (self.lane_width * 4)) // 2
        grid_x_end = grid_x_start + (self.lane_width * 4)

        if grid_x_start <= mx < grid_x_end:
            lane_idx = int((mx - grid_x_start) // self.lane_width)
            clicked_time_ms = self.current_time_ms + (receptor_y - my) / self.scroll_speed
            if clicked_time_ms >= 0:
                self.toggle_note_at_time(clicked_time_ms, lane_idx)

    def change_scroll_speed(self, delta):
        self.scroll_speed = max(0.1, round(self.scroll_speed + delta, 2))
        self.save_settings()

    def resync_audio_if_playing(self):
        if self.is_playing:
            self.play_start_time_ms = self.current_time_ms
            if self.song_path and os.path.isfile(self.song_path):
                try:
                    pygame.mixer.music.play(start=self.current_time_ms / 1000.0)
                except Exception:
                    pass

    def update(self):
        now = pygame.time.get_ticks()
        dt = now - self.last_ticks
        self.last_ticks = now

        if self.is_playing and not (self.selecting_chart or self.selecting_song):
            if pygame.mixer.music.get_busy():
                music_pos = pygame.mixer.music.get_pos()
                if music_pos >= 0:
                    self.current_time_ms = self.play_start_time_ms + float(music_pos)
            else:
                self.current_time_ms += dt

    def draw(self):
        screen_w, screen_h = self.screen.get_size()
        self.screen.fill((10, 10, 14))

        receptor_y = int(screen_h * 0.83)
        grid_x_start = (screen_w - (self.lane_width * 4)) // 2

        for i in range(4):
            x = grid_x_start + i * self.lane_width
            pygame.draw.rect(self.screen, (18, 20, 28), (x, 0, self.lane_width - 2, screen_h))

        snap_ms = self.get_snap_ms()
        visible_time_window = screen_h / self.scroll_speed
        min_time = self.current_time_ms - 200
        max_time = self.current_time_ms + visible_time_window

        first_snap = int(min_time // snap_ms) * snap_ms
        t = first_snap
        beat_ms = self.get_beat_ms()
        while t <= max_time:
            y = receptor_y - (t - self.current_time_ms) * self.scroll_speed
            if 0 <= y <= screen_h:
                is_full_beat = abs((t % beat_ms)) < 1.0 or abs((t % beat_ms) - beat_ms) < 1.0
                line_color = (70, 80, 105) if is_full_beat else (35, 40, 52)
                pygame.draw.line(self.screen, line_color, (grid_x_start, y), (grid_x_start + 4 * self.lane_width, y), 2 if is_full_beat else 1)
            t += snap_ms

        for time_ms, line in self.notes_dict.items():
            y = receptor_y - (time_ms - self.current_time_ms) * self.scroll_speed
            if -50 <= y <= screen_h + 50:
                for col_idx, char in enumerate(line):
                    if char in ['o', '1']:
                        x = grid_x_start + col_idx * self.lane_width + self.lane_width // 2
                        draw_smooth_circle(
                            self.screen,
                            LANE_COLORS[col_idx],
                            (x, y),
                            self.rec_radius,
                            outline_color=(255, 255, 255),
                            outline_thickness=2
                        )

        for i in range(4):
            x = grid_x_start + i * self.lane_width + self.lane_width // 2
            center = (x, receptor_y)
            draw_smooth_circle(
                self.screen,
                (25, 30, 42),
                center,
                self.rec_radius,
                outline_color=LANE_COLORS[i],
                outline_thickness=2
            )

        pygame.draw.line(self.screen, (255, 255, 255), (grid_x_start, receptor_y), (grid_x_start + 4 * self.lane_width, receptor_y), 2)

        panel_w = grid_x_start - 40
        if panel_w > 200:
            sidebar = pygame.Surface((panel_w, screen_h - 40), pygame.SRCALPHA)
            sidebar.fill((16, 18, 24, 220))
            self.screen.blit(sidebar, (20, 20))

            lines = [
                ("CHART EDITOR", (255, 215, 0), True),
                (f"File: {os.path.basename(self.filename)}", (200, 200, 210), False),
                (f"Song: {self.song_path or 'None'}", (200, 200, 210), False),
                (f"BPM: {self.bpm:.1f}", (200, 200, 210), False),
                (f"Scroll Speed: {self.scroll_speed:.2f}", (0, 230, 180), False),
                (f"Snap: 1/{self.snap_divisions[self.snap_idx]} Beat", (255, 255, 255), False),
                (f"Time: {int(self.current_time_ms)} ms", (180, 180, 200), False),
                ("", (0, 0, 0), False),
                ("CONTROLS:", (220, 220, 240), True),
                ("[L-Click] Place/Remove Note", (0, 230, 180), False),
                ("[Scroll] Snap Scroll", (160, 160, 180), False),
                ("[Shift+Scroll] Fine Scroll (10ms)", (255, 215, 0), False),
                ("[UP/DOWN] Change Scroll Speed", (160, 160, 180), False),
                ("[TAB] Change Snap", (160, 160, 180), False),
                ("[SPACE] Play / Pause", (160, 160, 180), False),
                ("[CTRL+S] Save Chart", (100, 220, 120), False),
                ("[O] Open Chart Selector", (0, 200, 255), False),
                ("[N] Create New Chart", (255, 180, 0), False)
            ]

            for idx, (txt, color, is_header) in enumerate(lines):
                f = self.big_font if is_header else self.font
                rendered = f.render(txt, True, color)
                self.screen.blit(rendered, (35, 35 + idx * 24))

        if self.selecting_chart:
            self.draw_chart_selector()
        elif self.selecting_song:
            self.draw_song_selector()

    def draw_chart_selector(self):
        screen_w, screen_h = self.screen.get_size()
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((5, 5, 10, 235))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 600, 450
        box_x, box_y = (screen_w - box_w) // 2, (screen_h - box_h) // 2
        pygame.draw.rect(self.screen, (24, 28, 40), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(self.screen, (0, 200, 255), (box_x, box_y, box_w, box_h), width=2, border_radius=12)

        title = self.big_font.render("SELECT CHART", True, (255, 215, 0))
        self.screen.blit(title, (box_x + 30, box_y + 25))

        subtitle = self.font.render("[UP/DOWN] Navigate | [ENTER] Load | [N] New | [ESC] Close", True, (160, 160, 180))
        self.screen.blit(subtitle, (box_x + 30, box_y + 65))

        pygame.draw.line(self.screen, (50, 60, 80), (box_x + 30, box_y + 95), (box_x + box_w - 30, box_y + 95), 1)

        item_y = box_y + 110
        if not self.available_charts:
            empty_txt = self.font.render("No charts found. Press [N] to create one!", True, (200, 100, 100))
            self.screen.blit(empty_txt, (box_x + 30, item_y))
        else:
            for idx, c_file in enumerate(self.available_charts):
                is_selected = (idx == self.selector_idx)
                bg_color = (40, 50, 75) if is_selected else (30, 35, 50)
                txt_color = (255, 255, 255) if is_selected else (170, 170, 185)

                rect_bounds = (box_x + 30, item_y, box_w - 60, 36)
                pygame.draw.rect(self.screen, bg_color, rect_bounds, border_radius=6)
                if is_selected:
                    pygame.draw.rect(self.screen, (0, 200, 255), rect_bounds, width=1, border_radius=6)

                txt = self.font.render(f"{'> ' if is_selected else '  '}{c_file}", True, txt_color)
                self.screen.blit(txt, (box_x + 40, item_y + 6))
                item_y += 42

    def draw_song_selector(self):
        screen_w, screen_h = self.screen.get_size()
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((5, 5, 10, 235))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 650, 500
        box_x, box_y = (screen_w - box_w) // 2, (screen_h - box_h) // 2
        pygame.draw.rect(self.screen, (24, 28, 40), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(self.screen, (39, 174, 96), (box_x, box_y, box_w, box_h), width=2, border_radius=12)

        title = self.big_font.render("SELECT AUDIO TRACK", True, (255, 215, 0))
        self.screen.blit(title, (box_x + 30, box_y + 25))

        subtitle = self.font.render("[UP/DOWN] Navigate | [ENTER] Attach Audio | [S] Skip Audio", True, (160, 160, 180))
        self.screen.blit(subtitle, (box_x + 30, box_y + 65))

        pygame.draw.line(self.screen, (50, 60, 80), (box_x + 30, box_y + 95), (box_x + box_w - 30, box_y + 95), 1)

        item_y = box_y + 110
        if not self.available_songs:
            empty_txt = self.font.render("No songs found. Place .mp3 or .wav files in current or /songs dir.", True, (200, 100, 100))
            self.screen.blit(empty_txt, (box_x + 30, item_y))
        else:
            for idx, s_file in enumerate(self.available_songs):
                is_selected = (idx == self.song_selector_idx)
                bg_color = (40, 75, 50) if is_selected else (30, 35, 50)
                txt_color = (255, 255, 255) if is_selected else (170, 170, 185)

                rect_bounds = (box_x + 30, item_y, box_w - 60, 36)
                pygame.draw.rect(self.screen, bg_color, rect_bounds, border_radius=6)
                if is_selected:
                    pygame.draw.rect(self.screen, (39, 174, 96), rect_bounds, width=1, border_radius=6)

                txt = self.font.render(f"{'> ' if is_selected else '  '}{s_file}", True, txt_color)
                self.screen.blit(txt, (box_x + 40, item_y + 6))
                item_y += 42


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("Pysu!Mania - Chart Editor")
    clock = pygame.time.Clock()

    editor = Editor(screen)
    editor.refresh_chart_list()

    if not editor.available_charts:
        print("No charts detected. Let's create your first chart!")
        editor.start_new_chart_flow()
        editor.refresh_chart_list()
    else:
        editor.load_chart(os.path.join(CHARTS_DIR, editor.available_charts[0]))

    running = True
    while running:
        clock.tick(FPS)
        editor.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not (editor.selecting_chart or editor.selecting_song):
                    mods = pygame.key.get_mods()
                    is_shift_down = bool(mods & pygame.KMOD_SHIFT)

                    if event.button == 1:
                        editor.handle_click(event.pos)

                    elif event.button == 4:
                        step = 10.0 if is_shift_down else editor.get_snap_ms()
                        editor.current_time_ms = max(0.0, editor.current_time_ms - step)
                        editor.resync_audio_if_playing()

                    elif event.button == 5:
                        step = 10.0 if is_shift_down else editor.get_snap_ms()
                        editor.current_time_ms += step
                        editor.resync_audio_if_playing()

            elif event.type == pygame.KEYDOWN:
                if editor.selecting_song:
                    if event.key == pygame.K_UP:
                        if editor.available_songs:
                            editor.song_selector_idx = (editor.song_selector_idx - 1) % len(editor.available_songs)

                    elif event.key == pygame.K_DOWN:
                        if editor.available_songs:
                            editor.song_selector_idx = (editor.song_selector_idx + 1) % len(editor.available_songs)

                    elif event.key == pygame.K_RETURN:
                        if editor.available_songs:
                            selected_song = editor.available_songs[editor.song_selector_idx]
                            editor.finalize_new_chart(selected_song)

                    elif event.key == pygame.K_s or event.key == pygame.K_ESCAPE:
                        editor.finalize_new_chart("")

                elif editor.selecting_chart:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_o:
                        editor.selecting_chart = False

                    elif event.key == pygame.K_UP:
                        if editor.available_charts:
                            editor.selector_idx = (editor.selector_idx - 1) % len(editor.available_charts)

                    elif event.key == pygame.K_DOWN:
                        if editor.available_charts:
                            editor.selector_idx = (editor.selector_idx + 1) % len(editor.available_charts)

                    elif event.key == pygame.K_RETURN:
                        if editor.available_charts:
                            selected_file = editor.available_charts[editor.selector_idx]
                            editor.load_chart(os.path.join(CHARTS_DIR, selected_file))
                            editor.selecting_chart = False

                    elif event.key == pygame.K_n:
                        editor.start_new_chart_flow()

                else:
                    if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        editor.save_chart()

                    elif event.key == pygame.K_o:
                        editor.refresh_chart_list()
                        editor.selecting_chart = True

                    elif event.key == pygame.K_n:
                        editor.start_new_chart_flow()

                    elif event.key == pygame.K_SPACE:
                        editor.is_playing = not editor.is_playing
                        if editor.is_playing:
                            editor.play_start_time_ms = editor.current_time_ms
                            if editor.song_path and os.path.isfile(editor.song_path):
                                try:
                                    pygame.mixer.music.play(start=editor.current_time_ms / 1000.0)
                                except Exception as e:
                                    print(f"[AUDIO WARN] Playback failed: {e}")
                        else:
                            pygame.mixer.music.stop()

                    elif event.key == pygame.K_TAB:
                        editor.snap_idx = (editor.snap_idx + 1) % len(editor.snap_divisions)

                    elif event.key == pygame.K_UP:
                        editor.change_scroll_speed(0.05)

                    elif event.key == pygame.K_DOWN:
                        editor.change_scroll_speed(-0.05)

                    elif event.key == pygame.K_PAGEUP:
                        editor.current_time_ms = max(0.0, editor.current_time_ms - editor.get_beat_ms() * 4)
                        editor.resync_audio_if_playing()

                    elif event.key == pygame.K_PAGEDOWN:
                        editor.current_time_ms += editor.get_beat_ms() * 4
                        editor.resync_audio_if_playing()

        editor.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
