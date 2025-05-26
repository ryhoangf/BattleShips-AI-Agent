import pygame
from engine import Game

pygame.init()
pygame.font.init()
font = pygame.font.SysFont("arial", 36)

# AI config
AI_MAP = {
    "random": lambda g: g.random_ai(),
    "basic": lambda g: g.basic_ai(),
    "proba": lambda g: g.probabilistic_ai()
}

AI_LABEL_MAP = {
    "easy": "random",
    "medium": "basic",
    "hard": "proba"
}

# GUI config
WIDTH, HEIGHT = 600, 400
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Battleship - AI Mode Selector")

WHITE = (255, 255, 255)
GREY = (40, 50, 60)
BLUE = (50, 150, 200)
GREEN = (50, 200, 150)

# Buttons
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.hovered = False

    def draw(self, surface):
        color = GREEN if self.hovered else BLUE
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        txt_surface = font.render(self.text, True, WHITE)
        surface.blit(txt_surface, (self.rect.x + 15, self.rect.y + 10))

    def is_hovered(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.hovered

# Game launcher
def launch_game(human1, human2, ai1=None, ai2=None):
    from battleship_gui import run_game_loop
    run_game_loop(human1, human2, ai1, ai2)

# Main menu logic
def main_menu():
    mode = None
    ai1, ai2 = None, None
    buttons = {
        "pve": Button((200, 80, 200, 50), "Player vs AI"),
        "ai_easy": Button((50, 160, 150, 50), "Easy (Random)"),
        "ai_medium": Button((225, 160, 150, 50), "Medium (Basic)"),
        "ai_hard": Button((400, 160, 150, 50), "Hard (Proba)"),
        "pvp": Button((200, 240, 200, 50), "AI vs AI")
    }

    running = True
    while running:
        SCREEN.fill(GREY)
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            for key, btn in buttons.items():
                if btn.is_clicked(event):
                    if key == "pve":
                        mode = "pve"
                    elif key.startswith("ai_") and mode == "pve":
                        label = key.split("_")[1]  # easy, medium, hard
                        ai2 = AI_LABEL_MAP[label]   # mapped to random, basic, proba
                        ai1 = None
                        launch_game(True, False, ai1, ai2)
                        running = False
                    elif key == "pvp":
                        mode = "pvp"
                        ai1 = select_ai("Select AI for Player 1")
                        ai2 = select_ai("Select AI for Player 2")
                        launch_game(False, False, ai1, ai2)
                        running = False

        for key, btn in buttons.items():
            btn.is_hovered(mouse_pos)
            if mode == "pve" and not key.startswith("ai_"):
                btn.draw(SCREEN)
            elif mode != "pve" and not key.startswith("ai_"):
                btn.draw(SCREEN)
            elif mode == "pve" and key.startswith("ai_"):
                btn.draw(SCREEN)

        pygame.display.flip()

# Simple dropdown AI chooser for PvP mode
def select_ai(title):
    clock = pygame.time.Clock()
    ai_buttons = {
        "random": Button((225, 100, 150, 50), "Random"),
        "basic": Button((225, 170, 150, 50), "Basic"),
        "proba": Button((225, 240, 150, 50), "Proba")
    }
    while True:
        SCREEN.fill(GREY)
        txt = font.render(title, True, WHITE)
        SCREEN.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 30))

        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            for key, btn in ai_buttons.items():
                if btn.is_clicked(event):
                    return key

        for btn in ai_buttons.values():
            btn.is_hovered(mouse_pos)
            btn.draw(SCREEN)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()