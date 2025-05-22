from engine import Game
import pygame

pygame.init()
pygame.font.init()
pygame.display.set_caption("Battleship")
font = pygame.font.SysFont("fresansttf", 100)


#global variables
SQSIZE = 45
H_MARGIN = SQSIZE*4
V_MARGIN = SQSIZE
WIDTH = SQSIZE*10*2 + H_MARGIN
HEIGHT = SQSIZE*10*2 + V_MARGIN
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
INDENT = 10
HUMAN1 = False
HUMAN2 = False

GREY = (40, 50, 60)
WHITE = (255, 250, 250)
GREEN = (50, 200, 150)
BLUE = (50, 150,200)
RED =(250, 50, 100)
ORANGE =(250, 140, 20)

COLORS = {"U": GREY, "M": BLUE, "H": ORANGE, "S": RED}

#draw grid function
def draw_grid(player, left = 0, top = 0, search = False):
    for i in range (100):
        x = left + i%10 * SQSIZE
        y = top + i//10 * SQSIZE
        square = pygame.Rect(x, y, SQSIZE, SQSIZE)
        pygame.draw.rect(SCREEN, WHITE, square, width = 3)
        if search:
            x += SQSIZE //2
            y += SQSIZE //2
            pygame.draw.circle(SCREEN, COLORS[player.search[i]], (x,y), radius=SQSIZE//4)

def draw_ships(player, left = 0, top = 0):
    for ship in player.ships:
        x = left + ship.col * SQSIZE + INDENT
        y = top + ship.row * SQSIZE + INDENT
        if ship.orientation == "h":
            width = ship.size *SQSIZE - 2*INDENT
            height = SQSIZE - 2*INDENT
        else:
            width = SQSIZE- 2*INDENT
            height = ship.size * SQSIZE- 2*INDENT
        rectangle = pygame.Rect(x,y, width,height)
        pygame.draw.rect(SCREEN, GREEN, rectangle, border_radius=15)

game = Game(HUMAN1, HUMAN2)

#game loop
animating = True
pausing = False

while animating:

    for event in pygame.event.get():
        
        if event.type == pygame.QUIT:
            animating = False
        
        #user click on mouse
        if event.type == pygame.MOUSEBUTTONDOWN and not game.over:
            x, y = pygame.mouse.get_pos()
            if game.player1_turn and x < SQSIZE * 10 and y < SQSIZE*10:
                row = y //SQSIZE
                col = x//SQSIZE
                index = row *10 + col
                game.make_move(index)
            elif not game.player1_turn and x > WIDTH -SQSIZE*10 and y> SQSIZE*10 + V_MARGIN:
                row = (y- SQSIZE*10 - V_MARGIN) //SQSIZE
                col = (x - SQSIZE*10 - H_MARGIN)//SQSIZE
                index = row *10 + col
                game.make_move(index)

        if event.type == pygame.KEYDOWN:
            #use escape key to clode the animation
            if event.key == pygame.K_ESCAPE:
                animating == False
            #use space bar to pause and unpause
            if event.key == pygame.K_SPACE:
                pausing = not pausing
            #use restart the game
            if event.key == pygame.K_RETURN:
                game = Game(HUMAN1, HUMAN2)
    
    if not pausing:
        SCREEN.fill(GREY)
        draw_grid(game.player1, search= True)
        draw_grid(game.player2, search= True, left = (WIDTH-H_MARGIN)//2 + H_MARGIN, top = (HEIGHT-V_MARGIN)//2 + V_MARGIN)
        draw_grid(game.player1, left = (WIDTH-H_MARGIN)//2 + H_MARGIN)
        draw_grid(game.player2, top = (HEIGHT-V_MARGIN)//2 + V_MARGIN)
        
        draw_ships(game.player1, top = (HEIGHT-V_MARGIN)//2 + V_MARGIN)
        draw_ships(game.player2, left = (WIDTH-H_MARGIN)//2 + H_MARGIN)
        
        #computer moves
        if not game.over and game.computer_turn:
            #chỗ này có thể thay đổi logic để xem các thuật toán random và basic thuật toán nào tốt hơn
            if game.player1_turn:
                game.random_ai()
            else:
                game.basic_ai()
            # game.basic_ai()
        #game over
        if game.over:
            text = "Player " + str(game.result) + " win!"
            textbox = font.render(text, False, GREY, WHITE)
            SCREEN.blit(textbox, (WIDTH//2 - 240, HEIGHT//2 - 50))
        
        pygame.time.wait(100)
        pygame.display.flip()