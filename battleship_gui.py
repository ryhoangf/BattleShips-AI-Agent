import pygame
from engine import Game

pygame.init()
pygame.font.init()

# Lấy kích thước màn hình thật
SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_info = pygame.display.Info()
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h

# Tính toán tự động kích thước lưới/bố cục để fit vừa mọi màn hình
PADDING = 48
GRID_ROWS = 2
GRID_COLS = 2
SQSIZE = min((WIDTH - 3 * PADDING) // (GRID_COLS * 10),
             (HEIGHT - 3 * PADDING - 200) // (GRID_ROWS * 10))

H_MARGIN = (WIDTH - 2 * SQSIZE * 10) // 3
V_MARGIN = (HEIGHT - 2 * SQSIZE * 10 - 200) // 3

label_font = pygame.font.SysFont("arial", max(18, SQSIZE // 2))
result_font = pygame.font.SysFont("arial", max(36, SQSIZE), bold=True)
stats_font = pygame.font.SysFont("arial", max(16, SQSIZE // 2))

# Colors
GREY = (40, 50, 60)
WHITE = (255, 250, 250)
GREEN = (50, 200, 150)
BLUE = (50, 150, 200)
RED = (250, 50, 100)
ORANGE = (250, 140, 20)
COLORS = {"U": GREY, "M": BLUE, "H": ORANGE, "S": RED}

AI_MAP = {
    "random": lambda g: g.random_ai(),
    "basic": lambda g: g.basic_ai(),
    "proba": lambda g: g.probabilistic_ai()
}

def count_sunk_ships(search, target_player):
    return sum(all(search[i] == "S" for i in ship.indexes) for ship in target_player.ships)

def draw_grid(player, left, top, search=True):
    for i in range(100):
        x = left + (i % 10) * SQSIZE
        y = top + (i // 10) * SQSIZE
        pygame.draw.rect(SCREEN, WHITE, (x, y, SQSIZE, SQSIZE), width=2)
        if search:
            cx = x + SQSIZE // 2
            cy = y + SQSIZE // 2
            pygame.draw.circle(SCREEN, COLORS[player.search[i]], (cx, cy), radius=SQSIZE // 4)

def draw_ships(player, left, top):
    INDENT = max(4, SQSIZE // 6)
    for ship in player.ships:
        x = left + ship.col * SQSIZE + INDENT
        y = top + ship.row * SQSIZE + INDENT
        if ship.orientation == "h":
            width = ship.size * SQSIZE - 2 * INDENT
            height = SQSIZE - 2 * INDENT
        else:
            width = SQSIZE - 2 * INDENT
            height = ship.size * SQSIZE - 2 * INDENT
        rectangle = pygame.Rect(x, y, width, height)
        pygame.draw.rect(SCREEN, GREEN, rectangle, border_radius=SQSIZE // 3)

def draw_labels(grid_pos):
    labels = [
        ("P1 Search", *grid_pos["p1_search"]),
        ("P2 Ships", *grid_pos["p2_ships"]),
        ("P1 Ships", *grid_pos["p1_ships"]),
        ("P2 Search", *grid_pos["p2_search"])
    ]
    for text, x, y in labels:
        txt = label_font.render(text, True, WHITE)
        SCREEN.blit(txt, (x, y - SQSIZE // 1.2))

def draw_legend():
    # Góc phải dưới cùng
    items = [("Miss", BLUE), ("Hit", ORANGE), ("Sunk", RED), ("Unknown", GREY)]
    box_size = max(16, SQSIZE // 2)
    gap = box_size + 8
    start_x = WIDTH - PADDING - 120
    start_y = HEIGHT - PADDING - len(items) * gap
    for i, (label, color) in enumerate(items):
        pygame.draw.rect(SCREEN, color, (start_x, start_y + i * gap, box_size, box_size), border_radius=3)
        txt = label_font.render(label, True, WHITE)
        SCREEN.blit(txt, (start_x + box_size + 8, start_y + i * gap - 2))

def draw_stats(game):
    p1_shots = game.shots_p1
    p2_shots = game.shots_p2
    p1_hits = sum(1 for s in game.player1.search if s in ("H", "S"))
    p2_hits = sum(1 for s in game.player2.search if s in ("H", "S"))
    p1_rate = p1_hits / p1_shots * 100 if p1_shots else 0
    p2_rate = p2_hits / p2_shots * 100 if p2_shots else 0
    p1_sunk = count_sunk_ships(game.player1.search, game.player2)
    p2_sunk = count_sunk_ships(game.player2.search, game.player1)

    stats1 = [
        f"PLAYER 1",
        f"Shots: {p1_shots}",
        f"Hits: {p1_hits}",
        f"Hit rate: {p1_rate:.1f}%",
        f"Ships sunk: {p1_sunk}/5"
    ]
    stats2 = [
        f"PLAYER 2",
        f"Shots: {p2_shots}",
        f"Hits: {p2_hits}",
        f"Hit rate: {p2_rate:.1f}%",
        f"Ships sunk: {p2_sunk}/5"
    ]
    base_y = HEIGHT - PADDING - len(stats1) * (SQSIZE // 1.1)
    for i, line in enumerate(stats1):
        txt = stats_font.render(line, True, WHITE)
        SCREEN.blit(txt, (PADDING, base_y + i * (SQSIZE // 1.1)))
    for i, line in enumerate(stats2):
        txt = stats_font.render(line, True, WHITE)
        SCREEN.blit(txt, (WIDTH // 2 + PADDING // 2, base_y + i * (SQSIZE // 1.1)))

def run_game_loop(human1, human2, ai1=None, ai2=None):
    game = Game(human1, human2)
    animating = True
    pausing = False

    # Tính vị trí 4 grid
    grid_w = SQSIZE * 10
    grid_h = SQSIZE * 10
    p1_search = (H_MARGIN, V_MARGIN)
    p2_ships = (H_MARGIN + grid_w + H_MARGIN, V_MARGIN)
    p1_ships = (H_MARGIN, V_MARGIN + grid_h + V_MARGIN)
    p2_search = (H_MARGIN + grid_w + H_MARGIN, V_MARGIN + grid_h + V_MARGIN)
    grid_pos = {
        "p1_search": p1_search,
        "p2_ships": p2_ships,
        "p1_ships": p1_ships,
        "p2_search": p2_search
    }

    while animating:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                animating = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    animating = False
                if event.key == pygame.K_SPACE:
                    pausing = not pausing
                if event.key == pygame.K_RETURN:
                    game = Game(human1, human2)

        if not pausing:
            SCREEN.fill(GREY)
            draw_labels(grid_pos)

            # 4 bảng
            draw_grid(game.player1, *grid_pos["p1_search"], search=True)
            draw_grid(game.player2, *grid_pos["p2_ships"], search=False)
            draw_grid(game.player1, *grid_pos["p1_ships"], search=False)
            draw_grid(game.player2, *grid_pos["p2_search"], search=True)
            draw_ships(game.player1, *grid_pos["p1_ships"])
            draw_ships(game.player2, *grid_pos["p2_ships"])

            # Chạy AI
            if not game.over:
                if not human1 and game.player1_turn:
                    AI_MAP[ai1](game)
                elif not human2 and not game.player1_turn:
                    AI_MAP[ai2](game)

            # Kết quả
            if game.over:
                text = f"Player {game.result} wins!"
                textbox = result_font.render(text, True, ORANGE)
                # Đặt ở giữa 4 bảng
                center_x = WIDTH // 2 - textbox.get_width() // 2
                center_y = HEIGHT // 2 - 70
                SCREEN.blit(textbox, (center_x, center_y))

            draw_stats(game)
            draw_legend()
            pygame.display.flip()
            pygame.time.wait(500)  # 500ms/lượt cho dễ quan sát

