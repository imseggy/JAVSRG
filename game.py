# The VSRG logic, so sigma, just like you :)

import os
import json
import pygame
import pygame.gfxdraw

from settings import (
    FPS, HEALTH_MAX, HIT_WINDOWS, DIRECTIONS,
    LANE_COLORS, LANE_HIGHLIGHT_COLORS
)
from note import Note
from utils import draw_smooth_circle, parse_line, list_json_files, get_song_title
from menus import song_selection_menu


def get_judgment(distance):
    if distance <= HIT_WINDOWS['sick']:
        return 'sick'
    elif distance <= HIT_WINDOWS['good']:
        return 'good'
    elif distance <= HIT_WINDOWS['bad']:
        return 'bad'
    elif distance <= HIT_WINDOWS['trash']:
        return 'trash'
    return 'miss'


def run_game_loop(screen, font, big_font, judg_font, settings):
    clock = pygame.time.Clock()

    json_files = list_json_files()
    song_titles = [get_song_title(f) for f in json_files]

    selected_json_file, settings = song_selection_menu(screen, font, big_font, json_files, song_titles, settings)

    key_mapping = settings["key_mapping"]
    key_to_dir = {v: k for k, v in key_mapping.items()}

    with open(selected_json_file, 'r') as f:
        song_data = json.load(f)

    music_sheet_raw = song_data.get('musicSheet', [])
    song_path = song_data.get('song', None)
    bpm = float(song_data.get('bpm', 120))

    lane_width = 92
    px_per_ms = settings["scroll_speed"]

    beat_interval_ms = 60000.0 / bpm
    parsed_sheet = []

    for i, item in enumerate(music_sheet_raw):
        if isinstance(item, dict):
            line_raw = item.get('line', item.get('notes', ''))
            time_ms = item.get('time', int(i * beat_interval_ms))
        else:
            line_raw = item
            time_ms = int(i * beat_interval_ms)

        parsed_sheet.append({"time": time_ms + settings["offset_ms"], "line": parse_line(line_raw)})

    parsed_sheet.sort(key=lambda x: x['time'])

    notes = []
    next_note_index = 0
    score = 0
    combo = 0
    max_combo = 0
    health = HEALTH_MAX
    hit_counts = {k: 0 for k in list(HIT_WINDOWS.keys()) + ['miss']}
    paused = False

    key_states = [False, False, False, False]

    judgment_text = ""
    judgment_color = (255, 255, 255)
    judgment_timer = 0

    game_state = 'playing'
    song_start_ticks = pygame.time.get_ticks()

    if song_path and os.path.isfile(song_path):
        try:
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.set_volume(settings["volume"])
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error loading song: {e}")

    running = True

    while running:
        clock.tick(FPS)
        screen_w, screen_h = screen.get_size()
        receptor_y = int(screen_h * 0.83)
        grid_x_start = (screen_w - (lane_width * 4)) // 2

        current_time_ms = pygame.time.get_ticks() - song_start_ticks if not paused else current_time_ms

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if event.key in key_to_dir:
                    dir_idx = DIRECTIONS.index(key_to_dir[event.key])
                    key_states[dir_idx] = True

                if event.key == pygame.K_F3:
                    px_per_ms = max(0.1, round(px_per_ms - 0.1, 2))
                elif event.key == pygame.K_F4:
                    px_per_ms = min(3.0, round(px_per_ms + 0.1, 2))

                if event.key == pygame.K_ESCAPE and game_state == 'playing':
                    paused = not paused
                    if paused:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()

                elif game_state == 'playing' and not paused and event.key in key_to_dir:
                    direction_str = key_to_dir[event.key]
                    dir_idx = DIRECTIONS.index(direction_str)

                    lane_notes = [n for n in notes if n.direction_idx == dir_idx]
                    closest_note = None
                    closest_dist = float('inf')

                    for n in lane_notes:
                        dist = abs(n.y - receptor_y)
                        if dist < closest_dist and dist <= HIT_WINDOWS['trash']:
                            closest_note = n
                            closest_dist = dist

                    if closest_note:
                        j = get_judgment(closest_dist)
                        hit_counts[j] += 1
                        judgment_text = j.upper()
                        judgment_timer = 20

                        if j == 'sick':
                            score += 300
                            combo += 1
                            health = min(HEALTH_MAX, health + 2)
                            judgment_color = (0, 255, 200)
                        elif j == 'good':
                            score += 200
                            combo += 1
                            health = min(HEALTH_MAX, health + 1)
                            judgment_color = (50, 220, 50)
                        elif j == 'bad':
                            score += 100
                            combo = 0
                            judgment_color = (230, 160, 40)
                        else:
                            score += 50
                            combo = 0
                            health -= 5
                            judgment_color = (200, 80, 80)

                        if combo > max_combo:
                            max_combo = combo
                        notes.remove(closest_note)
                    else:
                        hit_counts['miss'] += 1
                        combo = 0
                        health -= 10
                        judgment_text = "MISS"
                        judgment_color = (255, 50, 50)
                        judgment_timer = 20

                elif game_state == 'results':
                    if event.key == pygame.K_RETURN:
                        selected_json_file, settings = song_selection_menu(screen, font, big_font, json_files, song_titles, settings)
                        key_mapping = settings["key_mapping"]
                        key_to_dir = {v: k for k, v in key_mapping.items()}
                        px_per_ms = settings["scroll_speed"]

                        with open(selected_json_file, 'r') as f:
                            song_data = json.load(f)

                        music_sheet_raw = song_data.get('musicSheet', [])
                        song_path = song_data.get('song', None)
                        bpm = float(song_data.get('bpm', 120))
                        beat_interval_ms = 60000.0 / bpm

                        parsed_sheet.clear()
                        for i, item in enumerate(music_sheet_raw):
                            if isinstance(item, dict):
                                line_raw = item.get('line', item.get('notes', ''))
                                time_ms = item.get('time', int(i * beat_interval_ms))
                            else:
                                line_raw = item
                                time_ms = int(i * beat_interval_ms)
                            parsed_sheet.append({"time": time_ms + settings["offset_ms"], "line": parse_line(line_raw)})

                        parsed_sheet.sort(key=lambda x: x['time'])
                        notes.clear()
                        next_note_index = 0
                        score = 0
                        combo = 0
                        max_combo = 0
                        health = HEALTH_MAX
                        hit_counts = {k: 0 for k in list(HIT_WINDOWS.keys()) + ['miss']}
                        game_state = 'playing'
                        song_start_ticks = pygame.time.get_ticks()

                        if song_path and os.path.isfile(song_path):
                            try:
                                pygame.mixer.music.load(song_path)
                                pygame.mixer.music.set_volume(settings["volume"])
                                pygame.mixer.music.play()
                            except Exception:
                                pass

            elif event.type == pygame.KEYUP:
                if event.key in key_to_dir:
                    dir_idx = DIRECTIONS.index(key_to_dir[event.key])
                    key_states[dir_idx] = False

        if game_state == 'playing' and not paused:
            lookahead_ms = (screen_h + 100) / px_per_ms
            while next_note_index < len(parsed_sheet) and parsed_sheet[next_note_index]['time'] <= current_time_ms + lookahead_ms:
                item = parsed_sheet[next_note_index]
                for col_idx, char in enumerate(item['line']):
                    if char in ['o', '1']:
                        x = grid_x_start + col_idx * lane_width + lane_width // 2
                        notes.append(Note(col_idx, x, item['time']))
                next_note_index += 1

            for note in notes[:]:
                note.update_position(current_time_ms, receptor_y, px_per_ms)
                if note.y > receptor_y + HIT_WINDOWS['trash']:
                    notes.remove(note)
                    hit_counts['miss'] += 1
                    combo = 0
                    health -= 10
                    judgment_text = "MISS"
                    judgment_color = (255, 50, 50)
                    judgment_timer = 20

        if health <= 0 and game_state == 'playing':
            game_state = 'results'
            pygame.mixer.music.stop()

        if game_state == 'playing':
            if not pygame.mixer.music.get_busy() and next_note_index >= len(parsed_sheet) and not notes:
                game_state = 'results'

        screen.fill((10, 10, 14))

        if game_state == 'playing':
            for i in range(4):
                x = grid_x_start + i * lane_width
                pygame.draw.rect(screen, (18, 20, 28), (x, 0, lane_width - 2, screen_h))

            rec_radius = (lane_width - 14) // 2
            for i in range(4):
                x = grid_x_start + i * lane_width + lane_width // 2
                center = (x, receptor_y)

                is_pressed = key_states[i]

                bg_color = LANE_COLORS[i] if is_pressed else (25, 30, 42)
                border_color = (255, 255, 255) if is_pressed else LANE_COLORS[i]

                draw_smooth_circle(
                    screen,
                    bg_color,
                    center,
                    rec_radius,
                    outline_color=border_color,
                    outline_thickness=3 if is_pressed else 2
                )

                if is_pressed:
                    px, py = int(center[0]), int(center[1])
                    for t in range(2):
                        pygame.gfxdraw.aacircle(screen, px, py, rec_radius + 3 + t, LANE_HIGHLIGHT_COLORS[i])

            for note in notes:
                if -50 <= note.y <= screen_h + 50:
                    note.draw(screen, lane_width)

            score_lbl = font.render(f"SCORE: {score:07d}", True, (255, 255, 255))
            screen.blit(score_lbl, (20, 20))

            speed_display = px_per_ms * 10
            speed_lbl = font.render(f"SCROLL SPEED: {speed_display:.1f}", True, (180, 180, 200))
            screen.blit(speed_lbl, (20, 50))

            if combo > 0:
                combo_lbl = big_font.render(f"{combo}x", True, (255, 215, 0))
                screen.blit(combo_lbl, (grid_x_start + lane_width * 2 - combo_lbl.get_width() // 2, receptor_y - 240))

            if judgment_timer > 0 and judgment_text:
                j_surf = judg_font.render(judgment_text, True, judgment_color)
                screen.blit(j_surf, (grid_x_start + lane_width * 2 - j_surf.get_width() // 2, receptor_y - 190))
                judgment_timer -= 1

            hbar_w = 220
            hbar_h = 18
            pygame.draw.rect(screen, (30, 30, 40), (screen_w - hbar_w - 20, 20, hbar_w, hbar_h), border_radius=4)
            fill_w = int(hbar_w * max(0, health) / HEALTH_MAX)
            if fill_w > 0:
                pygame.draw.rect(screen, (0, 230, 120), (screen_w - hbar_w - 20, 20, fill_w, hbar_h), border_radius=4)

        elif game_state == 'results':
            title = big_font.render("RESULTS", True, (255, 255, 255))
            screen.blit(title, ((screen_w - title.get_width()) // 2, screen_h // 4))

            total_hits = sum(hit_counts[k] for k in ['sick', 'good', 'bad', 'trash', 'miss'])
            acc = 0.0
            if total_hits > 0:
                acc = (hit_counts['sick'] + 0.7 * hit_counts['good'] + 0.4 * hit_counts['bad'] + 0.1 * hit_counts['trash']) / total_hits * 100

            res_lines = [
                f"Score: {score}",
                f"Max Combo: {max_combo}",
                f"Accuracy: {acc:.2f}%",
                f"SICK: {hit_counts['sick']}  GOOD: {hit_counts['good']}  BAD: {hit_counts['bad']}  MISS: {hit_counts['miss']}"
            ]

            for i, line in enumerate(res_lines):
                txt = font.render(line, True, (200, 200, 210))
                screen.blit(txt, ((screen_w - txt.get_width()) // 2, screen_h // 2 - 20 + i * 40))

            retry = font.render("[ENTER] Return to Selection", True, (255, 215, 0))
            screen.blit(retry, ((screen_w - retry.get_width()) // 2, screen_h - 100))

        pygame.display.flip()
