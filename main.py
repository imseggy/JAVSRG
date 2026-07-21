import sys
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_STACK, load_settings
from game import run_game_loop


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Syncopation")

    font = pygame.font.SysFont(FONT_STACK, 22, bold=True)
    big_font = pygame.font.SysFont(FONT_STACK, 36, bold=True)
    judg_font = pygame.font.SysFont(FONT_STACK, 28, bold=True)

    settings = load_settings()

    run_game_loop(screen, font, big_font, judg_font, settings)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
