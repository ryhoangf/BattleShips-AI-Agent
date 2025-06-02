import pygame
from engine import Game

pygame.init()
pygame.font.init()

SCREEN_INFO = pygame.display.Info()
REAL_WIDTH, REAL_HEIGHT = SCREEN_INFO.current_w, SCREEN_INFO.current_h
SCREEN = pygame.display.set_mode((REAL_WIDTH, REAL_HEIGHT), pygame.FULLSCREEN)

SIDE_PADDING = 25; TOP_BANNER_HEIGHT = 75
BOTTOM_BANNER_HEIGHT = int(REAL_HEIGHT * 0.22)
if BOTTOM_BANNER_HEIGHT < 160: BOTTOM_BANNER_HEIGHT = 160

HORIZONTAL_GRID_PADDING_BETWEEN = SIDE_PADDING * 1.5
available_width_for_grids_block = REAL_WIDTH - 2 * SIDE_PADDING
VERTICAL_GRID_PADDING_BETWEEN = SIDE_PADDING * 1.5
available_height_for_grids_block = REAL_HEIGHT - TOP_BANNER_HEIGHT - BOTTOM_BANNER_HEIGHT
pre_label_font_size = max(18, int(REAL_HEIGHT * 0.025))
ESTIMATED_LABEL_HEIGHT_PER_ROW = pre_label_font_size * 1.3
sq_from_width = (available_width_for_grids_block - HORIZONTAL_GRID_PADDING_BETWEEN) / 20.0
height_for_actual_grids_and_padding = available_height_for_grids_block - 2 * ESTIMATED_LABEL_HEIGHT_PER_ROW - VERTICAL_GRID_PADDING_BETWEEN
sq_from_height = height_for_actual_grids_and_padding / 20.0
SQSIZE = int(min(sq_from_width, sq_from_height))
if SQSIZE < 12: SQSIZE = 12

label_font_size = max(18, int(SQSIZE * 0.45)); label_font = pygame.font.SysFont("arial", label_font_size, bold=True)
stats_font_size = max(16, int(SQSIZE * 0.4)); stats_font = pygame.font.SysFont("arial", stats_font_size)
turn_font_size = max(24, int(SQSIZE * 0.55)); turn_font = pygame.font.SysFont("arial", turn_font_size, bold=True)
result_font_size = max(40, int(SQSIZE * 0.9)); result_font = pygame.font.SysFont("arial", result_font_size, bold=True)
button_font_small_size = max(20, int(SQSIZE * 0.45)); button_font_small = pygame.font.SysFont("arial", button_font_small_size)
heat_value_font_size = max(10, int(SQSIZE * 0.25)); heat_value_font = pygame.font.SysFont("arial", heat_value_font_size)
analysis_font_size = max(14, int(SQSIZE * 0.3)); analysis_font = pygame.font.SysFont("arial", analysis_font_size)

GRID_ACTUAL_SIZE = SQSIZE * 10; ACTUAL_LABEL_HEIGHT_PER_ROW = label_font_size * 1.3
TOTAL_GRIDS_BLOCK_WIDTH = 2 * GRID_ACTUAL_SIZE + HORIZONTAL_GRID_PADDING_BETWEEN
GRID_BLOCK_START_X = (REAL_WIDTH - TOTAL_GRIDS_BLOCK_WIDTH) // 2
TOTAL_GRIDS_BLOCK_HEIGHT_NO_LABELS = 2 * GRID_ACTUAL_SIZE + VERTICAL_GRID_PADDING_BETWEEN
GRID_BLOCK_START_Y_NO_LABELS = TOP_BANNER_HEIGHT + (available_height_for_grids_block - TOTAL_GRIDS_BLOCK_HEIGHT_NO_LABELS - 2 * ACTUAL_LABEL_HEIGHT_PER_ROW) // 2
GRID_BLOCK_START_Y = GRID_BLOCK_START_Y_NO_LABELS # Grids themselves start here; labels are drawn above this Y

# Colors & AI Map (remain the same)
GREY_BG = (40, 50, 60); WHITE = (255, 250, 250)
GREEN_SHIP = (30, 200, 130); BLUE_MISS = (40, 150, 220)
RED_SUNK = (255, 50, 100); ORANGE_HIT = (255, 150, 30)
UNKNOWN_COLOR = (70, 80, 90); HIGHLIGHT_BORDER = (255, 255, 0)
BUTTON_COLOR_GAME = (100, 100, 150); BUTTON_HOVER_COLOR_GAME = (130, 130, 180)
COLORS = {"U": UNKNOWN_COLOR, "M": BLUE_MISS, "H": ORANGE_HIT, "S": RED_SUNK}
AI_MAP = { "random": lambda g: g.random_ai(), "basic": lambda g: g.basic_ai(), "proba": lambda g: g.probabilistic_ai(), "montecarlo": lambda g: g.monte_carlo_ai(), "bayes": lambda g: g.bayesian_ai() }

class InGameButton:
    def __init__(self, rect, text, font, tc=WHITE, bc=BUTTON_COLOR_GAME, hc=BUTTON_HOVER_COLOR_GAME): # Shorter param names
        self.rect=pygame.Rect(rect);self.text=text;self.font=font;self.tc=tc;self.bc=bc;self.hc=hc;self.hovered=False
    def draw(self, surf): # Shorter param name
        c=self.hc if self.hovered else self.bc;pygame.draw.rect(surf,c,self.rect,border_radius=8)
        ts=self.font.render(self.text,True,self.tc);tr=ts.get_rect(center=self.rect.center);surf.blit(ts,tr)
    def is_hovered(self,pos):self.hovered=self.rect.collidepoint(pos);return self.hovered
    def is_clicked(self,evt):return evt.type==pygame.MOUSEBUTTONDOWN and evt.button==1 and self.hovered # Shorter param name

def count_sunk_ships(search, target_player):return sum(all(search[i]=="S" for i in ship.indexes)for ship in target_player.ships)

# draw_grid (remains the same)

def draw_grid(player, left, top, search=True, is_active_player_grid=False, show_heat=True, heat_map=None):
    if search and is_active_player_grid:
        pygame.draw.rect(SCREEN, HIGHLIGHT_BORDER, (left - 3, top - 3, GRID_ACTUAL_SIZE + 6, GRID_ACTUAL_SIZE + 6), width=3, border_radius=5)
    for i in range(100):
        x = left + (i % 10) * SQSIZE
        y = top + (i // 10) * SQSIZE
        square_rect = pygame.Rect(x, y, SQSIZE, SQSIZE)
        pygame.draw.rect(SCREEN, COLORS["U"], square_rect)
        pygame.draw.rect(SCREEN, WHITE, square_rect, width=1)

        # Vẽ heat map chỉ khi là bảng Search!
        if show_heat and heat_map is not None and player.search[i] == "U":
            txt = stats_font.render(str(heat_map[i]), True, (255, 0, 0))
            SCREEN.blit(txt, txt.get_rect(center=(x + SQSIZE // 2, y + SQSIZE // 2)))

        if search and player.search[i] != "U":
            cx = x + SQSIZE // 2
            cy = y + SQSIZE // 2
            radius_factor = 0.35 if SQSIZE > 40 else 0.4
            pygame.draw.circle(SCREEN, COLORS[player.search[i]], (cx, cy), radius=int(SQSIZE * radius_factor))



# draw_ships (remains the same)
def draw_ships(player, left, top):
    INDENT = max(3, int(SQSIZE * 0.12))
    for ship in player.ships:
        x=left+ship.col*SQSIZE+ind;y=top+ship.row*SQSIZE+ind
        w=ship.size*SQSIZE-2*ind if ship.orientation=="h" else SQSIZE-2*ind # Shorter var name
        h=SQSIZE-2*ind if ship.orientation=="h" else ship.size*SQSIZE-2*ind # Shorter var name
        rect=pygame.Rect(x,y,w,h);pygame.draw.rect(SCREEN,GREEN_SHIP,rect,border_radius=max(5,int(SQSIZE*0.3)))

def draw_labels(grid_map):
    offset=int(ACTUAL_LABEL_HEIGHT_PER_ROW*0.15) # Shorter var name
    data=[("P1 Search",grid_map["p1_search"]),("P2 Ships",grid_map["p2_ships"]),
            ("P1 Ships",grid_map["p1_ships"]),("P2 Search",grid_map["p2_search"])] # Shorter var name
    for txt, (gx,gy) in data: # Shorter var names
        ts=label_font.render(txt,True,WHITE);lr=ts.get_rect(bottomleft=(gx,gy-offset)) # Shorter var names
        SCREEN.blit(ts,lr)

def draw_ai_analysis(game,p_num,area_r): # Shorter var names
    data=game.analysis_results.get(p_num);lines=[] # Shorter var names
    if not data:lines.append("Click 'Analyze' for AI insights.")
    else:
        rem_s=data.get("remaining_ships",[]);hot_sq=data.get("hottest_square",-1);max_h=data.get("max_heat_value",0) # Shorter var names
        lines.append("--- AI Analysis ---")
        if rem_s:lines.append(f"Opponent Ships Left: {', '.join(map(str,sorted(rem_s,reverse=True)))}")
        else:lines.append("All opponent ships likely sunk!")
        if hot_sq!=-1 and max_h>0:
            r,c=hot_sq//10,hot_sq%10;cc=chr(ord('A')+c);rc=str(r+1) # Shorter var names
            lines.append(f"Hottest Unknown: {cc}{rc} (Heat: {max_h})")
        else:lines.append("No clear hot spot found.")
    lh=analysis_font_size+3;pad=5 # Shorter var names
    for i,l in enumerate(lines):
        if area_r.top+pad+i*lh+analysis_font_size > area_r.bottom-pad:break
        ts=analysis_font.render(l,True,WHITE);SCREEN.blit(ts,(area_r.left+pad,area_r.top+pad+i*lh))

def draw_legend():
    items=[("Miss",BLUE_MISS),("Hit",ORANGE_HIT),("Sunk",RED_SUNK),("Unknown",UNKNOWN_COLOR)]
    bs=max(20,int(SQSIZE*0.5));t_gap=12;l_space=int(label_font_size*0.3) # Shorter var names
    sy=REAL_HEIGHT-BOTTOM_BANNER_HEIGHT+SIDE_PADDING//2 # Shorter var name
    max_w=label_font.render("Legend:",True,WHITE).get_width() # Shorter var name
    for lt,_ in items: # Shorter var names
        lw=label_font.render(lt,True,WHITE).get_width();ciw=bs+t_gap+lw # Shorter var names
        if ciw>max_w:max_w=ciw
    sx=REAL_WIDTH-SIDE_PADDING-max_w # Shorter var name
    ts=label_font.render("Legend:",True,WHITE);tr=ts.get_rect(topleft=(sx,sy));SCREEN.blit(ts,tr) # Shorter var names
    cy=tr.bottom+l_space+5 # Shorter var name
    for lt,color in items: # Shorter var names
        th=label_font.render(lt,True,WHITE).get_height();byo=(th-bs)//2 if th>bs else 0 # Shorter var names
        pygame.draw.rect(SCREEN,color,(sx,cy+byo,bs,bs),border_radius=3)
        ts=label_font.render(lt,True,WHITE);SCREEN.blit(ts,(sx+bs+t_gap,cy))
        cy+=max(th,bs)+l_space

def draw_stats(game):
    p1s,p2s=game.shots_p1,game.shots_p2;p1h,p2h=sum(1 for s in game.player1.search if s in("H","S")),sum(1 for s in game.player2.search if s in("H","S"))
    p1r,p2r=(p1h/p1s*100 if p1s else 0),(p2h/p2s*100 if p2s else 0)
    p1sk,p2sk=count_sunk_ships(game.player1.search,game.player2),count_sunk_ships(game.player2.search,game.player1)
    p1n,p2n=("PLAYER 1" if game.human1 else "AI 1"),("PLAYER 2" if game.human2 else "AI 2")
    s1d=[f"{p1n}",f"Shots: {p1s}",f"Hits: {p1h}",f"Rate: {p1r:.1f}%",f"Sunk: {p1sk}/5"]
    s2d=[f"{p2n}",f"Shots: {p2s}",f"Hits: {p2h}",f"Rate: {p2r:.1f}%",f"Sunk: {p2sk}/5"]
    lh=stats_font_size+int(stats_font_size*0.3);sy=REAL_HEIGHT-BOTTOM_BANNER_HEIGHT+SIDE_PADDING//2 # Shorter var names
    p1mw=0 # Shorter var name
    for i,l in enumerate(s1d):
        s=stats_font.render(l,True,WHITE); # Shorter var name
        if s.get_width()>p1mw:p1mw=s.get_width()
        SCREEN.blit(s,(SIDE_PADDING,sy+i*lh))
    p2sx=SIDE_PADDING+p1mw+SIDE_PADDING*2 # Shorter var name
    for i,l in enumerate(s2d):s=stats_font.render(l,True,WHITE);SCREEN.blit(s,(p2sx,sy+i*lh)) # Shorter var name

def draw_turn_indicator(game):
    if game.over:return
    p,t=("P1" if game.player1_turn else "P2"),("(H)" if (game.player1_turn and game.human1)or(not game.player1_turn and game.human2) else "(AI)") # Shorter var names
    ts=turn_font.render(f"Turn: {p} {t}",True,HIGHLIGHT_BORDER);tr=ts.get_rect(center=(REAL_WIDTH//2,TOP_BANNER_HEIGHT//2));SCREEN.blit(ts,tr) # Shorter var names

def run_game_loop(human1,human2,ai1_name=None,ai2_name=None):
    game=Game(human1,human2);anim=True;paus=False;clk=pygame.time.Clock() # Shorter var names
    btn_w,btn_h=int(SQSIZE*4),int(SQSIZE*1.0)
    exit_br=pygame.Rect(REAL_WIDTH-btn_w-SIDE_PADDING,(TOP_BANNER_HEIGHT-btn_h)//2,btn_w,btn_h) # Shorter var name
    exit_btn=InGameButton(exit_br,"Exit Menu",button_font_small) # Shorter var name
    abw,abh=int(SQSIZE*3.8),int(SQSIZE*0.9);aby=(TOP_BANNER_HEIGHT-abh)//2 # Shorter var names
    ap1b,ap2b=None,None # Shorter var names
    if human1:ap1b=InGameButton(pygame.Rect(SIDE_PADDING,aby,abw,abh),"P1 Analyze",button_font_small)
    if human2:p2ax=SIDE_PADDING+(abw+SIDE_PADDING//2 if human1 else 0);ap2b=InGameButton(pygame.Rect(p2ax,aby,abw,abh),"P2 Analyze",button_font_small) # Shorter var names
    adw,adh=int(REAL_WIDTH*0.30),int(BOTTOM_BANNER_HEIGHT*0.9);adx=REAL_WIDTH//2-adw//2 # Shorter var names
    ady=REAL_HEIGHT-BOTTOM_BANNER_HEIGHT+(BOTTOM_BANNER_HEIGHT-adh)//2 # Shorter var name
    adar=pygame.Rect(adx,ady,adw,adh);pra=0 # Shorter var names
    g1x,g2x=GRID_BLOCK_START_X,GRID_BLOCK_START_X+GRID_ACTUAL_SIZE+HORIZONTAL_GRID_PADDING_BETWEEN # Shorter var names
    gr1y,gr2y=(GRID_BLOCK_START_Y+ACTUAL_LABEL_HEIGHT_PER_ROW),(GRID_BLOCK_START_Y+ACTUAL_LABEL_HEIGHT_PER_ROW+GRID_ACTUAL_SIZE+VERTICAL_GRID_PADDING_BETWEEN+ACTUAL_LABEL_HEIGHT_PER_ROW) # Shorter var names
    gm={"p1_search":(g1x,gr1y),"p2_ships":(g2x,gr1y),"p1_ships":(g1x,gr2y),"p2_search":(g2x,gr2y)} # Shorter var name
    p1sr,p2sr=pygame.Rect(*gm["p1_search"],GRID_ACTUAL_SIZE,GRID_ACTUAL_SIZE),pygame.Rect(*gm["p2_search"],GRID_ACTUAL_SIZE,GRID_ACTUAL_SIZE) # Shorter var names
    pygame.display.set_caption(f"Battleship! (SQ: {SQSIZE})")
    hm_p1,hm_p2=None,None # Shorter var names for heatmaps

    while anim:
        mp,mc=pygame.mouse.get_pos(),False # Shorter var names
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT: pygame.quit(); exit()
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_ESCAPE: animating = False
                if evt.key == pygame.K_SPACE: pausing = not pausing
                if evt.key == pygame.K_RETURN and game.over: game=Game(human1,human2); pausing=False
            exit_button.is_hovered(m_pos)
            if exit_button.is_clicked(evt): animating=False
            if evt.type == pygame.MOUSEBUTTONDOWN and evt.button==1 and not pausing and not game.over:
                m_clk=True
                if game.human1 and game.player1_turn and p1_sr.collidepoint(m_pos):
                    c=(m_pos[0]-p1_sr.left)//SQSIZE; r=(m_pos[1]-p1_sr.top)//SQSIZE
                    if 0<=r<10 and 0<=c<10 and game.player1.search[r*10+c]=='U': game.make_move(r*10+c)
                elif game.human2 and not game.player1_turn and p2_sr.collidepoint(m_pos):
                    c=(m_pos[0]-p2_sr.left)//SQSIZE; r=(m_pos[1]-p2_sr.top)//SQSIZE
                    if 0<=r<10 and 0<=c<10 and game.player2.search[r*10+c]=='U': game.make_move(r*10+c)
        if not animating: break

        if not pausing:
            SCREEN.fill(GREY_BG)
            # Ở trong run_game_loop, mỗi frame:
            heat_map = None
            if not game.over:
                is_ai_turn = (not human1 and game.player1_turn and ai1_name == "proba") or (not human2 and not game.player1_turn and ai2_name == "proba")
                if is_ai_turn:
                    heat_map = game.compute_heat_map()
            # Draw top banner elements
            draw_turn_indicator(game)
            exit_button.draw(SCREEN)
            
            # Draw grid block (labels then grids)
            draw_labels(grid_map)
           # Player 1 Search
            draw_grid(
                game.player1,
                *grid_map["p1_search"],
                search=True,
                is_active_player_grid=game.player1_turn,
                show_heat=(game.player1_turn and heat_map is not None),
                heat_map=(heat_map if game.player1_turn else None)
            )
            # Player 2 Ships (không bao giờ show heat)
            draw_grid(game.player2, *grid_map["p2_ships"], search=False, show_heat=False)
            # Player 1 Ships (không bao giờ show heat)
            draw_grid(game.player1, *grid_map["p1_ships"], search=False, show_heat=False)
            # Player 2 Search
            draw_grid(
                game.player2,
                *grid_map["p2_search"],
                search=True,
                is_active_player_grid=not game.player1_turn,
                show_heat=(not game.player1_turn and heat_map is not None),
                heat_map=(heat_map if not game.player1_turn else None)
            )


            
            is_aivai_mode = not game.human1 and not game.human2
            
            if game.human1 or game.over or is_aivai_mode: draw_ships(game.player1,*grid_map["p1_ships"])
            if game.human2 or game.over or is_aivai_mode: draw_ships(game.player2,*grid_map["p2_ships"])

            is_h_turn = (game.human1 and game.player1_turn) or (game.human2 and not game.player1_turn)

# AI move logic with 1-second delay
            if not game.over and not is_h_turn:
                if not ai_waiting:
                    ai_waiting = True
                    ai_wait_start = pygame.time.get_ticks()
                else:
                    if pygame.time.get_ticks() - ai_wait_start >= 1000:  # Delay 1s
                        if not human1 and game.player1_turn and ai1_name:
                           AI_MAP[ai1_name](game)
                        elif not human2 and not game.player1_turn and ai2_name:
                            AI_MAP[ai2_name](game)
                        ai_waiting = False

            
            # Game Over Text (if applicable)
            if game.over:
                wt=("P1 WINS!" if game.human1 else "AI 1 WINS!")if game.result==1 else("P2 WINS!" if game.human2 else "AI 2 WINS!") # Shorter var name
                ts=result_font.render(wt,True,ORANGE_HIT); # Shorter var name
                mgy=GRID_BLOCK_START_Y+ACTUAL_LABEL_HEIGHT_PER_ROW+GRID_ACTUAL_SIZE+VERTICAL_GRID_PADDING_BETWEEN//2 # Shorter var name
                tr=ts.get_rect(center=(REAL_WIDTH//2,mgy));SCREEN.blit(ts,tr) # Shorter var names
                ags=label_font.render("ENTER to Play Again",True,WHITE);agr=ags.get_rect(center=(REAL_WIDTH//2,tr.bottom+int(SQSIZE*0.7))) # Shorter var names
                SCREEN.blit(ags,agr)
            draw_stats(game);draw_legend();pygame.display.flip()
        clk.tick(60);cd=10 # Shorter var names
        if not paus and not game.over:
            ishtd=(game.human1 and game.player1_turn)or(game.human2 and not game.player1_turn) # Shorter var name
            if not ishtd:pass
            elif ishtd and not mc:cd=30
        elif paus:cd=100
        pygame.time.wait(cd)