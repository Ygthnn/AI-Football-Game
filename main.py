#!/usr/bin/env python3
"""
main.py – Human (RED) vs PPO Agent (BLUE) • 1-v-1 Football
"""

from __future__ import annotations
import os, sys, random
from pathlib import Path
import numpy as np
import pygame
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

# ── project / asset directories ───────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR   = PROJECT_ROOT / "assets"
MODELS_DIR   = PROJECT_ROOT / "models"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── local modules ────────────────────────────────────────────────
from core.stadium        import Stadium
from core.ball           import Ball
from core.player         import Player
from core.team           import Team
from controllers.human_controller import HumanController
from ui.menu             import Menu
from ui.score_panel      import ScorePanel
from utils.save_load     import save_game, load_game, list_users
from rl_agent.environment import FootballEnv

# ── window & match constants ─────────────────────────────────────
W, H       = 800, 600
TOP_MARGIN = ScorePanel.H               # 40 px HUD bar
FIELD_H    = H - TOP_MARGIN
MATCH_MS   = 180_000                    # 3 minutes
FPS        = 60

# ── pygame init ──────────────────────────────────────────────────
os.environ.pop("SDL_VIDEODRIVER", None)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
pygame.init(); pygame.mixer.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("GOALAI Football 1-v-1")
clock = pygame.time.Clock()

# ── graphics & sounds ────────────────────────────────────────────
pitch_img = pygame.transform.scale(
    pygame.image.load(ASSETS_DIR / "pitch.png").convert(), (W, FIELD_H)
)
goal_sounds = [pygame.mixer.Sound(ASSETS_DIR / f)
               for f in ("goal_cheer1.wav", "goal_cheer2.wav")]
for s in goal_sounds: s.set_volume(0.7)

pygame.mixer.music.load(ASSETS_DIR / "menu_music.mp3")
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)

# ── menu ─────────────────────────────────────────────────────────
menu = Menu(screen)
username, cont = menu.run(bool(list_users()))
if username is None:
    pygame.quit(); sys.exit()
pygame.mixer.music.stop()

# ── entities ─────────────────────────────────────────────────────
stadium = Stadium(W, FIELD_H)
ball = Ball(W//2, TOP_MARGIN + FIELD_H//2, radius=6)

START_RED, START_BLUE = (100, TOP_MARGIN+FIELD_H//2), (700, TOP_MARGIN+FIELD_H//2)
red_p  = Player(*START_RED,  "red",  False, "You")
blue_p = Player(*START_BLUE, "blue", True,  "AI")
red_t, blue_t = Team("red",[red_p]), Team("blue",[blue_p])

human_ctrl = HumanController(red_p, {
    "up":pygame.K_w, "down":pygame.K_s,
    "left":pygame.K_a, "right":pygame.K_d,
    "kick":pygame.K_LSHIFT, "pass":pygame.K_e, "tackle":pygame.K_q
})

# ── PPO agent ────────────────────────────────────────────────────
ckpt = max(MODELS_DIR.glob("*.zip"), key=os.path.getmtime)
print("✅ loading agent:", ckpt.name)
agent: PPO = PPO.load(ckpt, device="cpu")

venv = DummyVecEnv([lambda: FootballEnv(phase=2)])
vec_file = MODELS_DIR / "final_vecnorm.pkl"
if vec_file.exists():
    venv = VecNormalize.load(vec_file, venv)
    venv.training = False; venv.norm_reward = False
    print("✅ VecNormalize loaded")
else:
    print("⚠ VecNormalize not found – raw obs will be used")

# ── HUD / score panel ────────────────────────────────────────────
font_hud = pygame.font.Font(None, 46)
panel = ScorePanel(W, font_hud)

# ── confetti helper (unchanged) ──────────────────────────────────
def play_goal_effect():
    cx, cy = W//2, TOP_MARGIN + FIELD_H//2
    parts = [{"x":cx,"y":cy,
              "vx":random.uniform(-3,3),"vy":random.uniform(-8,-3),
              "col":random.choice([(255,0,0),(0,255,0),(0,0,255),
                                   (255,255,0),(255,165,0),(128,0,128)]),
              "life":60} for _ in range(150)]
    snd = random.choice(goal_sounds); snd.play()
    txt = pygame.font.Font(None,120).render("GOAAAALL!",True,(255,215,0))
    rect= txt.get_rect(center=(W//2, H//2))
    start=pygame.time.get_ticks(); DUR=2000
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
        screen.blit(pitch_img,(0,TOP_MARGIN))
        ball.draw(screen); red_t.draw(screen); blue_t.draw(screen)
        alive=False
        for p in parts:
            if p["life"]>0:
                p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["vy"]+=0.25; p["life"]-=1
                pygame.draw.rect(screen,p["col"],(int(p["x"]),int(p["y"]),8,8))
                alive=True
        el=pygame.time.get_ticks()-start
        if el<DUR:
            fade=txt.copy(); fade.set_alpha(255-int(255*el/DUR))
            screen.blit(fade,rect)
        elif snd.get_num_channels()==0 and not alive:
            break
        pygame.display.flip(); clock.tick(FPS)

# ── pause menu (hover+click sounds) ──────────────────────────────
hover_snd = pygame.mixer.Sound(ASSETS_DIR/"ui_hover.wav")
click_snd = pygame.mixer.Sound(ASSETS_DIR/"ui_click.wav")
hover_snd.set_volume(0.4); click_snd.set_volume(0.5)

def pause_menu()->str:
    f_big,f_sml=pygame.font.Font(None,48),pygame.font.Font(None,36)
    rects={k:pygame.Rect(300,200+i*70,200,50)
           for i,k in enumerate(("continue","restart","save_quit"))}
    hover_state={}
    while True:
        screen.fill((240,240,255))
        screen.blit(f_big.render("Game Paused",True,(0,0,80)),(290,120))
        mpos=pygame.mouse.get_pos()
        for k,r in rects.items():
            hov=r.collidepoint(mpos)
            if hov and not hover_state.get(k,False): hover_snd.play()
            hover_state[k]=hov
            pygame.draw.rect(screen,(200,220,255) if hov else (255,255,255),r)
            screen.blit(f_sml.render(k.replace('_',' ').title(),True,(0,0,0)),
                        (r.x+20,r.y+10))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: return "save_quit"
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return "continue"
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                for k,r in rects.items():
                    if r.collidepoint(e.pos): click_snd.play(); return k

# ── snapshot helpers ─────────────────────────────────────────────
start_ms = pygame.time.get_ticks()
if cont and (sav := load_game(username)):
    ball.x, ball.y = sav["ball"]
    red_p.x, red_p.y = sav["red"]
    blue_p.x, blue_p.y = sav["blue"]
    stadium.score_red = sav["score_red"]; stadium.score_blue = sav["score_blue"]
    start_ms = pygame.time.get_ticks() - sav.get("elapsed_ms", 0)

snapshot = lambda:{ "ball":(ball.x,ball.y), "red":(red_p.x,red_p.y),
                    "blue":(blue_p.x,blue_p.y),
                    "score_red":stadium.score_red,
                    "score_blue":stadium.score_blue,
                    "elapsed_ms":pygame.time.get_ticks()-start_ms }

# ── main loop ────────────────────────────────────────────────────
running=True
while running:
    clock.tick(FPS)
    keys=pygame.key.get_pressed()

    if keys[pygame.K_ESCAPE]:
        act=pause_menu()
        if act=="restart":
            stadium.score_red=stadium.score_blue=0
            ball.x,ball.y=W//2,TOP_MARGIN+FIELD_H//2
            red_p.x,red_p.y=START_RED; blue_p.x,blue_p.y=START_BLUE
            start_ms=pygame.time.get_ticks()
        elif act=="save_quit":
            save_game(snapshot(),username); break
        continue

    for e in pygame.event.get():
        if e.type==pygame.QUIT: save_game(snapshot(),username); running=False

    # time-up?
    if pygame.time.get_ticks()-start_ms>=MATCH_MS:
        save_game(snapshot(),username); break

    # user & agent
    human_ctrl.handle_input(keys,ball)
    obs=np.array([[blue_p.x,blue_p.y,ball.x,ball.y,
                   ball.vel_x/10,ball.vel_y/10]],np.float32)
    if isinstance(venv,VecNormalize): obs=venv.normalize_obs(obs)
    act=int(agent.predict(obs,deterministic=True)[0])
    if act==1: blue_p.move("up")
    elif act==2: blue_p.move("down")
    elif act==3: blue_p.move("left")
    elif act==4: blue_p.move("right")
    elif act==5: blue_p.kick_ball(ball)

    # physics
    ball.move()
    # ---------- NEW boundary clamp so ball never enters HUD strip ----------
    if ball.y - ball.radius < TOP_MARGIN:
        ball.y = TOP_MARGIN + ball.radius
        ball.vel_y *= -1
    elif ball.y + ball.radius > TOP_MARGIN + FIELD_H:
        ball.y = TOP_MARGIN + FIELD_H - ball.radius
        ball.vel_y *= -1
    # ----------------------------------------------------------------------

    # goal?
    if stadium.check_goal(ball):
        panel.trigger(stadium.score_red,stadium.score_blue)
        play_goal_effect()
        stadium.reset_ball_position(ball)
        ball.x,ball.y=W//2,TOP_MARGIN+FIELD_H//2
        red_p.x,red_p.y=START_RED; blue_p.x,blue_p.y=START_BLUE

    # draw
    panel.draw(screen,stadium.score_red,stadium.score_blue,clock)
    rem=max(0,(MATCH_MS-(pygame.time.get_ticks()-start_ms))//1000)
    mm,ss=divmod(rem,60)
    timer=font_hud.render(f"{mm:02d}:{ss:02d}",True,(255,255,255))
    screen.blit(timer,timer.get_rect(center=(W//2,TOP_MARGIN//2)))

    screen.blit(pitch_img,(0,TOP_MARGIN))
    ball.draw(screen); red_t.draw(screen); blue_t.draw(screen)
    pygame.display.flip()

pygame.quit()
print("🏁 Game ended – thanks for playing!")