# Trust in yourself :)

import sys
import pygame
from settings import FPS, CHARTS_DIR, DIRECTIONS, save_settings


def settings_menu(screen, font, big_font, settings):
    """Full-featured interactive settings screen."""
    clock = pygame.time.Clock()
    selected_option = 0
    rebinding_dir = None

    options = [
        "Rebind Left Key",
        "Rebind Down Key",
        "Rebind Up Key",
        "Rebind Right Key",
        "Music Volume",
        "Scroll Speed",
        "Audio Offset (ms)",
        "Save & Exit"
    ]

    while True:
        screen.fill((12, 12, 18))
        screen_w, screen_h = screen.get_size()

        title = big_font.render("SETTINGS", True, (255, 255, 255))
        screen.blit(title, ((screen_w - title.get_width()) // 2, 50))

        key_bind_vals = [
            pygame.key.name(settings["key_mapping"]["left"]).upper(),
            pygame.key.name(settings["key_mapping"]["down"]).upper(),
            pygame.key.name(settings["key_mapping"]["up"]).upper(),
            pygame.key.name(settings["key_mapping"]["right"]).upper(),
            f"{int(settings['volume'] * 100)}%",
            f"{settings['scroll_speed'] * 10:.1f}",
            f"{settings['offset_ms']} ms",
            ""
        ]

        for i, opt in enumerate(options):
            is_sel = (i == selected_option)
            color = (255, 215, 0) if is_sel else (180, 180, 195)

            if rebinding_dir and i < 4 and DIRECTIONS[i] == rebinding_dir:
                val_str = "[PRESS ANY KEY]"
                color = (255, 80, 80)
            else:
                val_str = key_bind_vals[i]

            prefix = "> " if is_sel else "  "
            label = font.render(f"{prefix}{opt}", True, color)
            val = font.render(val_str, True, (240, 240, 240) if is_sel else (140, 140, 160))

            y_pos = 150 + i * 44
            screen.blit(label, (screen_w // 4, y_pos))
            screen.blit(val, (screen_w * 3 // 4 - val.get_width(), y_pos))

        instr_text = "[UP/DOWN] Move  [LEFT/RIGHT] Adjust  [ENTER] Select  [ESC] Cancel"
        if rebinding_dir:
            instr_text = "Press any key to rebind action..."

        instr = font.render(instr_text, True, (140, 140, 160))
        screen.blit(instr, ((screen_w - instr.get_width()) // 2, screen_h - 60))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if rebinding_dir:
                    if event.key != pygame.K_ESCAPE:
                        settings["key_mapping"][rebinding_dir] = event.key
                    rebinding_dir = None
                    continue

                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)

                elif event.key == pygame.K_LEFT:
                    if selected_option == 4:  # Volume
                        settings["volume"] = max(0.0, round(settings["volume"] - 0.05, 2))
                    elif selected_option == 5:  # Scroll Speed
                        settings["scroll_speed"] = max(0.1, round(settings["scroll_speed"] - 0.1, 2))
                    elif selected_option == 6:  # Offset
                        settings["offset_ms"] -= 5

                elif event.key == pygame.K_RIGHT:
                    if selected_option == 4:  # Volume
                        settings["volume"] = min(1.0, round(settings["volume"] + 0.05, 2))
                    elif selected_option == 5:  # Scroll Speed
                        settings["scroll_speed"] = min(3.0, round(settings["scroll_speed"] + 0.1, 2))
                    elif selected_option == 6:  # Offset
                        settings["offset_ms"] += 5

                elif event.key == pygame.K_RETURN:
                    if selected_option < 4:
                        rebinding_dir = DIRECTIONS[selected_option]
                    elif selected_option == 7:  # Save and exit
                        save_settings(settings)
                        return settings

                elif event.key == pygame.K_ESCAPE:
                    save_settings(settings)
                    return settings

        clock.tick(FPS)


def song_selection_menu(screen, font, big_font, json_files, song_titles, settings):
    selected = 0
    clock = pygame.time.Clock()

    while True:
        screen.fill((12, 12, 16))

        title_text = big_font.render("SELECT CHART", True, (255, 255, 255))
        screen.blit(title_text, ((screen.get_width() - title_text.get_width()) // 2, 60))

        if not json_files:
            no_song_text = font.render(f"No charts found in '{CHARTS_DIR}/'!", True, (255, 80, 80))
            screen.blit(no_song_text, ((screen.get_width() - no_song_text.get_width()) // 2, 200))
        else:
            for i, title in enumerate(song_titles):
                is_sel = (i == selected)
                color = (255, 215, 0) if is_sel else (180, 180, 195)
                prefix = "> " if is_sel else "  "
                text = font.render(f"{prefix}{title}", True, color)
                screen.blit(text, (screen.get_width() // 4, 180 + i * 42))

        instr = font.render("[UP/DOWN] Select   [ENTER] Play   [TAB / S] Settings", True, (140, 140, 160))
        screen.blit(instr, ((screen.get_width() - instr.get_width()) // 2, screen.get_height() - 70))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and json_files:
                    selected = (selected - 1) % len(json_files)
                elif event.key == pygame.K_DOWN and json_files:
                    selected = (selected + 1) % len(json_files)
                elif event.key in (pygame.K_TAB, pygame.K_s):
                    settings = settings_menu(screen, font, big_font, settings)
                elif event.key == pygame.K_RETURN and json_files:
                    return json_files[selected], settings

        clock.tick(FPS)
