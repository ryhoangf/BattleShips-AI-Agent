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
GRID_BLOCK_START_Y = GRID_BLOCK_START_Y_NO_LABELS

GREY_BG=(40,50,60); WHITE=(255,250,250); GREEN_SHIP=(30,200,130); BLUE_MISS=(40,150,220); RED_SUNK=(255,50,100)
ORANGE_HIT=(255,150,30); UNKNOWN_COLOR=(70,80,90); HIGHLIGHT_BORDER=(255,255,0)
BUTTON_COLOR_GAME=(100,100,150); BUTTON_HOVER_COLOR_GAME=(130,130,180)
HEAT_TEXT_COLOR_LOW=(180,180,180); HEAT_TEXT_COLOR_HIGH=(255,255,100)
COLORS={"U":UNKNOWN_COLOR,"M":BLUE_MISS,"H":ORANGE_HIT,"S":RED_SUNK}
AI_MAP={"random":lambda g:g.random_ai(),"basic":lambda g:g.basic_ai(),"proba":lambda g:g.probabilistic_ai()}

class InGameButton:
    def __init__(self, rect, text, font, tc=WHITE, bc=BUTTON_COLOR_GAME, hc=BUTTON_HOVER_COLOR_GAME): # Shorter param names
        self.rect=pygame.Rect(rect);self.text=text;self.font=font;self.tc=tc;self.bc=bc;self.hc=hc;self.hovered=False
    def draw(self, surf): # Shorter param name
        c=self.hc if self.hovered else self.bc;pygame.draw.rect(surf,c,self.rect,border_radius=8)
        ts=self.font.render(self.text,True,self.tc);tr=ts.get_rect(center=self.rect.center);surf.blit(ts,tr)
    def is_hovered(self,pos):self.hovered=self.rect.collidepoint(pos);return self.hovered
    def is_clicked(self,evt):return evt.type==pygame.MOUSEBUTTONDOWN and evt.button==1 and self.hovered # Shorter param name

def count_sunk_ships(search, target_player):return sum(all(search[i]=="S" for i in ship.indexes)for ship in target_player.ships)

def draw_grid(player, left, top, search=True, active_grid=False, heat_map=None): # Renamed params
    if search and active_grid:pygame.draw.rect(SCREEN,HIGHLIGHT_BORDER,(left-3,top-3,GRID_ACTUAL_SIZE+6,GRID_ACTUAL_SIZE+6),width=3,border_radius=5)
    for i in range(100):
        x=left+(i%10)*SQSIZE;y=top+(i//10)*SQSIZE;sq_r=pygame.Rect(x,y,SQSIZE,SQSIZE) # Shorter var names
        pygame.draw.rect(SCREEN,COLORS["U"],sq_r);pygame.draw.rect(SCREEN,WHITE,sq_r,width=1)
        if search:
            if player.search[i]!="U":
                cx=x+SQSIZE//2;cy=y+SQSIZE//2;rad_f=0.35 if SQSIZE>40 else 0.4 # Shorter var name
                pygame.draw.circle(SCREEN,COLORS[player.search[i]],(cx,cy),radius=int(SQSIZE*rad_f))
            elif heat_map and heat_map[i]>0:
                hv=heat_map[i];tc=HEAT_TEXT_COLOR_HIGH if hv>20 else HEAT_TEXT_COLOR_LOW # Shorter var names
                if hv<5:tc=(130,130,130)
                hs=heat_value_font.render(str(hv),True,tc);hr=hs.get_rect(center=(x+SQSIZE//2,y+SQSIZE//2)) # Shorter var names
                SCREEN.blit(hs,hr)

def draw_ships(player,left,top):
    ind=max(3,int(SQSIZE*0.12)) # Shorter var name
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
            if evt.type==pygame.QUIT:pygame.quit();exit()
            if evt.type==pygame.KEYDOWN:
                if evt.key==pygame.K_ESCAPE:anim=False
                if evt.key==pygame.K_SPACE:paus=not paus
                if evt.key==pygame.K_RETURN and game.over:game=Game(human1,human2);paus=False;hm_p1,hm_p2=None,None;pra=0 # Reset analysis on new game
            exit_btn.is_hovered(mp);
            if exit_btn.is_clicked(evt):anim=False
            if ap1b:
                ap1b.is_hovered(mp)
                if ap1b.is_clicked(evt) and game.player1_turn:res=game.analyze_opponent_board(1);pra=1;hm_p1=res.get("heat_map")if res else None;hm_p2=None # Shorter var names
            if ap2b:
                ap2b.is_hovered(mp)
                if ap2b.is_clicked(evt) and not game.player1_turn:res=game.analyze_opponent_board(2);pra=2;hm_p2=res.get("heat_map")if res else None;hm_p1=None # Shorter var names
            if evt.type==pygame.MOUSEBUTTONDOWN and evt.button==1 and not paus and not game.over:
                mc=True
                if game.human1 and game.player1_turn and p1sr.collidepoint(mp):
                    c,r=(mp[0]-p1sr.left)//SQSIZE,(mp[1]-p1sr.top)//SQSIZE # Shorter var names
                    if 0<=r<10 and 0<=c<10 and game.player1.search[r*10+c]=='U':game.make_move(r*10+c);hm_p1=None;pra=0 # Clear heatmap on move
                elif game.human2 and not game.player1_turn and p2sr.collidepoint(mp):
                    c,r=(mp[0]-p2sr.left)//SQSIZE,(mp[1]-p2sr.top)//SQSIZE # Shorter var names
                    if 0<=r<10 and 0<=c<10 and game.player2.search[r*10+c]=='U':game.make_move(r*10+c);hm_p2=None;pra=0 # Clear heatmap on move
        if not anim:break
        if not paus:
            SCREEN.fill(GREY_BG);draw_turn_indicator(game);exit_btn.draw(SCREEN)
            if ap1b:ap1b.draw(SCREEN)
            if ap2b:ap2b.draw(SCREEN)
            draw_labels(gm)
            cp1h=hm_p1 if game.player1_turn and pra==1 else None # Shorter var names
            cp2h=hm_p2 if not game.player1_turn and pra==2 else None # Shorter var names
            draw_grid(game.player1,*gm["p1_search"],search=True,active_grid=game.player1_turn,heat_map=cp1h)
            draw_grid(game.player2,*gm["p2_ships"],search=False)
            draw_grid(game.player1,*gm["p1_ships"],search=False)
            draw_grid(game.player2,*gm["p2_search"],search=True,active_grid=not game.player1_turn,heat_map=cp2h)
            aivai=not game.human1 and not game.human2 # Shorter var name
            if game.human1 or game.over or aivai:draw_ships(game.player1,*gm["p1_ships"])
            if game.human2 or game.over or aivai:draw_ships(game.player2,*gm["p2_ships"])
            isht=(game.human1 and game.player1_turn)or(game.human2 and not game.player1_turn) # Shorter var name
            if not game.over and not isht:
                pygame.time.wait(1000)
                if not human1 and game.player1_turn and ai1_name:AI_MAP[ai1_name](game)
                elif not human2 and not game.player1_turn and ai2_name:AI_MAP[ai2_name](game)
            if pra!=0:draw_ai_analysis(game,pra,adar)
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