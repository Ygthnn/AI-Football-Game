# main.py – Human (RED) vs PPO Agent (BLUE) – 1-v-1 Football
# ───────────────────────────────────────────────────────────

from __future__ import annotations
import os, sys, random
from pathlib import Path
import os
os.environ.pop("SDL_VIDEODRIVER", None)
import numpy as np
import pygame
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

# ────────── project-local imports ──────────
from core.stadium      import Stadium
from core.ball         import Ball
from core.player       import Player
from core.team         import Team
from controllers.human_controller import HumanController
from ui.menu           import Menu
from utils.save_load   import save_game, load_game, list_users
from rl_agent.environment import FootballEnv               # only for obs shape

# ★★★ kick / catch radius used in-game ★★★
CATCH_R_GAME = 45      # px   (≈ the 30-px radius used during training)

# ────────── constants / window ──────────
W, H       = 800, 600
TOP_MARGIN = 40
FIELD_H    = H - TOP_MARGIN
MATCH_MS   = 180_000
FPS        = 60

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
pygame.init(); pygame.mixer.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("GOALAI Football 1-v-1")
clock = pygame.time.Clock()

# ────────── assets ──────────
raw_pitch = pygame.image.load(os.path.join("assets", "pitch.png")).convert()
pitch_img = pygame.transform.scale(raw_pitch, (W, FIELD_H))

goal_sounds = [pygame.mixer.Sound(os.path.join("assets", f))
               for f in ("goal_cheer1.wav", "goal_cheer2.wav")]
for s in goal_sounds: s.set_volume(0.7)

pygame.mixer.music.load(os.path.join("assets", "menu_music.mp3"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# ────────── menu ──────────
menu = Menu(screen)
username, cont = menu.run(bool(list_users()))
if username is None:
    pygame.mixer.music.stop(); pygame.quit(); sys.exit()
pygame.mixer.music.stop()

# ────────── entities / teams ──────────
stadium = Stadium(W, FIELD_H)
ball    = Ball(W//2, TOP_MARGIN + FIELD_H//2)

START_RED, START_BLUE = (100, TOP_MARGIN+FIELD_H//2), (700, TOP_MARGIN+FIELD_H//2)
red_player  = Player(*START_RED,  "red",  False, "You")
blue_player = Player(*START_BLUE, "blue", True,  "AI")

red_team  = Team("red",  [red_player])
blue_team = Team("blue", [blue_player])

human_ctrl = HumanController(
    red_player,
    {"up":pygame.K_w, "down":pygame.K_s, "left":pygame.K_a, "right":pygame.K_d,
     "kick":pygame.K_LSHIFT, "pass":pygame.K_e, "tackle":pygame.K_q}
)

# ────────── RL-agent loading ──────────
MODELS_DIR = Path("models")
ckpt = max(MODELS_DIR.glob("**/*.zip"), key=os.path.getmtime, default=None)
if ckpt is None:
    raise FileNotFoundError("❌ No PPO checkpoint (*.zip) found in ./models")
print(f"✅ Loading PPO checkpoint: {ckpt.name}")

PHASE_TO_WATCH = 2
def _build_env(): return FootballEnv(phase=PHASE_TO_WATCH, render_mode=None)

venv_raw = DummyVecEnv([_build_env])
vec_file = MODELS_DIR / "final_vecnorm.pkl"
if vec_file.exists():
    venv = VecNormalize.load(vec_file, venv_raw)
    venv.training, venv.norm_reward = False, False
    print(f"✅ Loaded VecNormalize stats: {vec_file.name}")
else:
    venv = venv_raw
    print("⚠ VecNormalize not found – agent will use raw observations")

agent: PPO = PPO.load(
    ckpt,
    env=venv,
    device="cpu",
    custom_objects={"learning_rate": 0.0, "clip_range": 0.0}
)

# ────────── confetti helper (unchanged) ──────────
class ConfettiParticle:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -3)
        self.color = random.choice([
            (255,0,0), (0,255,0), (0,0,255),
            (255,255,0), (255,165,0), (128,0,128)])
        self.life = 60
    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.2; self.life -= 1
    def draw(self, surf):
        if self.life > 0:
            pygame.draw.rect(surf, self.color,
                             (int(self.x), int(self.y), 8, 8))

def play_confetti_and_text(screen, clock, pitch, ball, red_t, blue_t, sounds, n=150):
    cx, cy = W//2, TOP_MARGIN + FIELD_H//2
    parts  = [ConfettiParticle(cx, cy) for _ in range(n)]
    font   = pygame.font.Font(None, 120)
    txt    = font.render("GOAAAALL!", True, (255,215,0))
    rect   = txt.get_rect(center=(W//2, H//2))
    dur, start = 2000, pygame.time.get_ticks()
    snd = random.choice(sounds); snd.play()
    while True:
        el = pygame.time.get_ticks() - start
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        screen.blit(pitch, (0, TOP_MARGIN))
        ball.draw(screen); red_t.draw(screen); blue_t.draw(screen)
        alive = False
        for p in parts:
            p.update()
            if p.life > 0: p.draw(screen); alive = True
        if el < dur:
            fade = txt.copy(); fade.set_alpha(max(0, 255 - int(255*el/dur)))
            screen.blit(fade, rect)
        elif snd.get_num_channels() <= 0 and not alive:
            break
        pygame.display.flip(); clock.tick(60)

# ────────── fonts ──────────
font_score = pygame.font.Font(None, 46)
font_clk   = pygame.font.Font(None, 46)
font_end   = pygame.font.Font(None, 72)

# ────────── resume save ──────────
start_ms = pygame.time.get_ticks()
if cont and (sav := load_game(username)):
    ball.x, ball.y                 = sav["ball"]
    red_player.x, red_player.y     = sav["red"]
    blue_player.x, blue_player.y   = sav["blue"]
    stadium.score_red              = sav["score_red"]
    stadium.score_blue             = sav["score_blue"]
    start_ms = pygame.time.get_ticks() - sav.get("elapsed_ms", 0)

snapshot = lambda : {
    "ball": (ball.x, ball.y),
    "red":  (red_player.x,  red_player.y),
    "blue": (blue_player.x, blue_player.y),
    "score_red":  stadium.score_red,
    "score_blue": stadium.score_blue,
    "elapsed_ms": pygame.time.get_ticks() - start_ms,
}
dist = lambda a,b: ((a.x-b.x)**2 + (a.y-b.y)**2)**0.5

# ────────── main loop ──────────
running = True
while running:
    clock.tick(FPS)
    keys = pygame.key.get_pressed()

    if keys[pygame.K_ESCAPE]:
        save_game(snapshot(), username); break
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            save_game(snapshot(), username); running = False

    # possession flags (match env logic but with slightly looser radius)
    red_player.has_ball  = dist(red_player,  ball) < CATCH_R_GAME
    blue_player.has_ball = dist(blue_player, ball) < CATCH_R_GAME

    # timer
    elapsed = pygame.time.get_ticks() - start_ms
    if elapsed >= MATCH_MS:
        winner = "Red" if stadium.score_red > stadium.score_blue else \
                 "Blue" if stadium.score_blue > stadium.score_red else "No one"
        msg = "Draw!" if winner == "No one" else f"{winner} won!"
        for _ in range(180):
            screen.fill((0,0,0))
            surf = font_end.render(msg, True, (255,255,255))
            screen.blit(surf, surf.get_rect(center=(W//2, H//2)))
            pygame.display.flip(); clock.tick(60)
        save_game(snapshot(), username); break

    # user controls
    human_ctrl.handle_input(keys, ball)

    # RL-agent decision
    obs = np.array([[
        blue_player.x,
        blue_player.y - TOP_MARGIN,
        ball.x,
        ball.y - TOP_MARGIN,
        np.clip(ball.vel_x/10.0, -1, 1),
        np.clip(ball.vel_y/10.0, -1, 1)]], dtype=np.float32)
    if isinstance(venv, VecNormalize):
        obs = venv.normalize_obs(obs)
    act = int(agent.predict(obs, deterministic=True)[0])

    if   act == 1: blue_player.move("up")
    elif act == 2: blue_player.move("down")
    elif act == 3: blue_player.move("left")
    elif act == 4: blue_player.move("right")
    elif act == 5 and blue_player.has_ball:        # ← kicks again!
        blue_player.kick_ball(ball)

    # physics & goals
    ball.move()
    if stadium.check_goal(ball):
        play_confetti_and_text(screen, clock, pitch_img, ball,
                               red_team, blue_team, goal_sounds)
        stadium.reset_ball_position(ball)
        ball.x, ball.y = W//2, TOP_MARGIN + FIELD_H//2
        red_player.x, red_player.y   = START_RED
        blue_player.x, blue_player.y = START_BLUE

    # top UI bar
    screen.fill((30,30,30), (0,0,W,TOP_MARGIN))
    pygame.draw.rect(screen, (200,0,0), (10,5,110,TOP_MARGIN-10))
    pygame.draw.rect(screen, (0,0,200), (W-120,5,110,TOP_MARGIN-10))
    screen.blit(font_score.render(str(stadium.score_red),  True, (255,255,255)),
                (20,5))
    screen.blit(font_score.render(str(stadium.score_blue), True, (255,255,255)),
                (W-60,5))
    rem = max(0, MATCH_MS - elapsed)//1000; mm, ss = divmod(rem, 60)
    screen.blit(font_clk.render(f"{mm:02d}:{ss:02d}", True, (255,255,255)),
                (W//2 - 30, 5))

    # pitch & entities
    screen.blit(pitch_img, (0, TOP_MARGIN))
    ball.draw(screen); red_team.draw(screen); blue_team.draw(screen)
    pygame.display.flip()

pygame.quit()
print("🏁 Game ended – thanks for playing!")
