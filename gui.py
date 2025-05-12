import pygame

pygame.init()
pygame.display.set_caption("Battleship")

#global variables
SQSIZE = 45
H_MARGIN = SQSIZE*4
V_MARGIN = SQSIZE
WIDTH = SQSIZE*10*2 + H_MARGIN
HEIGHT = SQSIZE*10*2 + V_MARGIN
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

GREY = (40, 50, 60)
WHITE = (255, 250, 250)

#draw grid function
def draw_grid(left = 0, top = 0):
    for i in range (100):
        x = left + i%10 * SQSIZE
        y = top + i//10 * SQSIZE
        square = pygame.Rect(x, y, SQSIZE, SQSIZE)
        pygame.draw.rect(SCREEN, WHITE, square, width = 3)

#game loop
animating = True
pausing = False

while animating:

    for event in pygame.event.get():
        
        if event.type == pygame.QUIT:
            animating = False
        
        if event.type == pygame.KEYDOWN:
            #use escape key to clode the animation
            if event.key == pygame.K_ESCAPE:
                animating == False
            #use space bar to pause and unpause
            if event.key == pygame.K_SPACE:
                pausing = not pausing
    
    if not pausing:
        SCREEN.fill(GREY)
        draw_grid()
        draw_grid(left = (WIDTH-H_MARGIN)//2 + H_MARGIN, top = (HEIGHT-V_MARGIN)//2 + V_MARGIN)
        draw_grid(left = (WIDTH-H_MARGIN)//2 + H_MARGIN)
        draw_grid(top = (HEIGHT-V_MARGIN)//2 + V_MARGIN)
        pygame.display.flip()