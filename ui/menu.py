# ui/menu.py
from __future__ import annotations
import os, pygame
from pathlib import Path
from utils.save_load import list_users, delete_game

# ─────────────────────────── PROJE & ASSET YOLLARI ──────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent          # …/AI‑Football‑Game
ASSETS_DIR   = PROJECT_ROOT / "assets"                         # tek asset klasörü

BG_FILE   = ASSETS_DIR / "menu_bg1.png"
LOGO_FILE = ASSETS_DIR / "logo.png"
HOVER_SND = ASSETS_DIR / "ui_hover.wav"
CLICK_SND = ASSETS_DIR / "ui_click.wav"

SCROLL_STEP = 50   # mouse‑wheel başına piksel

# ────────────────────────────── MENU SINIFI ─────────────────────────────────
class Menu:
    BLUE_BG   = (200, 230, 255)
    BTN_BG    = (255, 255, 255)
    BTN_HOVER = (180, 200, 225)
    TXT_COLOR = (0, 0, 0)

    def __init__(self, screen: pygame.Surface):
        self.sc        = screen
        self.W, self.H = screen.get_size()

        # Fonts
        self.font     = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 64)

        # Text input
        self.input_box   = pygame.Rect(self.W//2 - 100, self.H//2 + 140, 200, 40)
        self.color_inact = pygame.Color("#A9CCE3")
        self.color_act   = pygame.Color("#4B9CD3")
        self.color       = self.color_inact
        self.active = False
        self.text   = ""

        # State
        self.done = False
        self.cont_flag = False
        self.pick_name = None
        self.mode = "main"                 # main / new / load
        self.last_mode_switch_time = 0

        # Graphics
        self.bg   = pygame.transform.scale(pygame.image.load(BG_FILE), (self.W, self.H))
        self.logo = pygame.image.load(LOGO_FILE)
        lw = self.W // 4
        lh = int(self.logo.get_height() * (lw / self.logo.get_width()))
        self.logo = pygame.transform.scale(self.logo, (lw, lh))
        self.logo_alpha = 0
        self.fade_in_speed = 3

        # Sounds
        self.snd_hover = pygame.mixer.Sound(HOVER_SND)
        self.snd_click = pygame.mixer.Sound(CLICK_SND)
        self.snd_hover.set_volume(0.4)
        self.snd_click.set_volume(0.5)

        # Saved games + scroll
        self.scroll_y = 0
        self._refresh_users()

    # ───────────── yardımcılar ─────────────
    def _refresh_users(self):
        self.users = list_users()
        self.scroll_y = 0
        self._recompute_rects()

    def _recompute_rects(self):
        base_y = self.H//2 + 40 + self.scroll_y
        self.user_rects = [
            pygame.Rect(self.W//2-100, base_y + i*50, 200, 40)
            for i in range(len(self.users))
        ]
        self.del_rects = [
            pygame.Rect(self.W//2+110, base_y + i*50 + 10, 20, 20)
            for i in range(len(self.users))
        ]

    def _play_hover_once(self, key: str, is_hover: bool):
        if not hasattr(self, "_hover_state"):
            self._hover_state = {}
        prev = self._hover_state.get(key, False)
        if is_hover and not prev:
            self.snd_hover.play()
        self._hover_state[key] = is_hover

    # ───────────── ana döngü ─────────────
    def run(self, _has_saves: bool):
        clock  = pygame.time.Clock()
        volume = pygame.mixer.music.get_volume()

        while not self.done:
            now = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()

            # ---- events ----
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); exit()

                # scroll (sadece load ekranında)
                if ev.type == pygame.MOUSEWHEEL and self.mode == "load":
                    self.scroll_y += -ev.y * SCROLL_STEP
                    self.scroll_y = min(0, self.scroll_y)   # yukarı sınır
                    self._recompute_rects()

                # mouse click
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    back_rect = pygame.Rect(20, 20, 220, 50)
                    if self.mode in ('new','load') and back_rect.collidepoint(ev.pos):
                        self.snd_click.play()
                        self.mode = "main"; self.text = ""; self.active = False
                        continue

                    # MAIN ekranı
                    if self.mode == "main":
                        btns = {
                            "new" : pygame.Rect(self.W//2-100, self.H//2+30 ,200,40),
                            "load": pygame.Rect(self.W//2-100, self.H//2+90 ,200,40),
                            "quit": pygame.Rect(self.W//2-100, self.H//2+150,200,40),
                        }
                        if   btns["new"].collidepoint(ev.pos):
                            self.snd_click.play()
                            self.mode = "new";  self.last_mode_switch_time = now
                        elif btns["load"].collidepoint(ev.pos):
                            self.snd_click.play()
                            self.mode = "load"; self.last_mode_switch_time = now
                            self._refresh_users()
                        elif btns["quit"].collidepoint(ev.pos):
                            self.snd_click.play(); pygame.quit(); exit()

                    # NEW ekranı
                    if self.mode == "new":
                        self.active = self.input_box.collidepoint(ev.pos)
                        self.color  = self.color_act if self.active else self.color_inact

                        # Start Game düğmesi
                        start_rect = pygame.Rect(self.W//2-80,
                                                 self.input_box.y+60, 160, 40)
                        if start_rect.collidepoint(ev.pos) and self.text.strip():
                            self.snd_click.play()
                            self.done = True

                    # LOAD ekranı
                    if self.mode == "load" and now - self.last_mode_switch_time > 200:
                        for name, r, dr in zip(self.users, self.user_rects, self.del_rects):
                            if r.collidepoint(ev.pos):
                                self.snd_click.play()
                                self.pick_name, self.cont_flag = name, True
                                self.done = True
                            if dr.collidepoint(ev.pos):
                                self.snd_click.play()
                                delete_game(name); self._refresh_users()
                                break

                # klavye
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_PLUS, pygame.K_KP_PLUS):
                        volume = min(1.0, volume+0.1); pygame.mixer.music.set_volume(volume)
                    elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        volume = max(0.0, volume-0.1); pygame.mixer.music.set_volume(volume)

                    if self.mode == "new" and self.active:
                        if   ev.key == pygame.K_RETURN and self.text.strip():
                            self.snd_click.play(); self.done = True
                        elif ev.key == pygame.K_BACKSPACE:
                            self.text = self.text[:-1]
                        else:
                            self.text += ev.unicode

            # ---- logo fade ----
            if self.logo_alpha < 255:
                self.logo_alpha = min(255, self.logo_alpha + self.fade_in_speed)
                self.logo.set_alpha(self.logo_alpha)

            # ---- draw ----
            self.sc.blit(self.bg, (0,0))
            self.sc.blit(self.logo, ((self.W - self.logo.get_width())//2, 50))
            title = self.big_font.render("Goalai", True, (0,255,255))
            self.sc.blit(title, title.get_rect(center=(self.W//2, self.H-80)))

            # MAIN -------------
            if self.mode == "main":
                btns = {"new":(self.H//2+30,"Start New Game"),
                        "load":(self.H//2+90,"Load Game"),
                        "quit":(self.H//2+150,"Quit")}
                for key,(y,label) in btns.items():
                    rect = pygame.Rect(self.W//2-100, y, 200, 40)
                    hov = rect.collidepoint(mouse_pos)
                    self._play_hover_once(key, hov)
                    color = self.BTN_HOVER if hov else self.BTN_BG
                    draw  = rect.inflate(10,10) if hov else rect
                    pygame.draw.rect(self.sc, color, draw, border_radius=6)
                    txt = self.font.render(label, True, self.TXT_COLOR)
                    self.sc.blit(txt, (draw.x+(draw.w-txt.get_width())//2,
                                       draw.y+(draw.h-txt.get_height())//2))

            # LOAD -------------
            elif self.mode == "load":
                head = self.font.render("Select a saved game", True, (0,255,255))
                self.sc.blit(head, head.get_rect(center=(self.W//2, self.H//2+10)))

                for name, r, dr in zip(self.users, self.user_rects, self.del_rects):
                    hov = r.collidepoint(mouse_pos)
                    self._play_hover_once(name, hov)
                    color = self.BTN_HOVER if hov else self.BTN_BG
                    draw  = r.inflate(10,10) if hov else r
                    pygame.draw.rect(self.sc, color, draw, border_radius=6)
                    txt = self.font.render(name, True, self.TXT_COLOR)
                    self.sc.blit(txt, (draw.x+(draw.w-txt.get_width())//2,
                                       draw.y+(draw.h-txt.get_height())//2))

                    # delete
                    d_hov = dr.collidepoint(mouse_pos)
                    self._play_hover_once(f"{name}_del", d_hov)
                    d_col = self.BTN_HOVER if d_hov else (255,80,80)
                    d_draw= dr.inflate(6,6) if d_hov else dr
                    pygame.draw.rect(self.sc, d_col, d_draw, border_radius=4)
                    x_s = self.font.render("x", True, (255,255,255))
                    self.sc.blit(x_s, (d_draw.x+(d_draw.w-x_s.get_width())//2,
                                       d_draw.y+(d_draw.h-x_s.get_height())//2))

            # NEW --------------
            elif self.mode == "new":
                # metin kutusu
                txt = self.font.render(self.text, True, self.TXT_COLOR)
                self.input_box.w = max(200, txt.get_width()+10)
                self.sc.blit(txt, (self.input_box.x+5, self.input_box.y+5))
                pygame.draw.rect(self.sc, self.color, self.input_box, 2, border_radius=4)
                self._play_hover_once("input", self.input_box.collidepoint(mouse_pos))

                # Start Game düğmesi
                start_rect = pygame.Rect(self.W//2-80, self.input_box.y+60, 160, 40)
                hov      = start_rect.collidepoint(mouse_pos)
                enabled  = bool(self.text.strip())

                if enabled:
                    color = self.BTN_HOVER if hov else self.BTN_BG
                else:
                    color = (200,200,200)          # pasif gri

                self._play_hover_once("start", hov and enabled)
                draw = start_rect.inflate(10,10) if (hov and enabled) else start_rect
                pygame.draw.rect(self.sc, color, draw, border_radius=6)

                txt_col = (100,100,100) if not enabled else self.TXT_COLOR
                txt_s   = self.font.render("Start Game", True, txt_col)
                self.sc.blit(txt_s, (draw.x+(draw.w-txt_s.get_width())//2,
                                     draw.y+(draw.h-txt_s.get_height())//2))

            # Back button (load/new)
            if self.mode in ("new","load"):
                br = pygame.Rect(20,20,220,50)
                hov = br.collidepoint(mouse_pos)
                self._play_hover_once("back", hov)
                color = self.BTN_HOVER if hov else self.BTN_BG
                draw  = br.inflate(10,10) if hov else br
                pygame.draw.rect(self.sc, color, draw, border_radius=6)
                txt = self.font.render("Back to Menu", True, self.TXT_COLOR)
                self.sc.blit(txt, (draw.x+(draw.w-txt.get_width())//2,
                                   draw.y+(draw.h-txt.get_height())//2))

            # volume slider
            bar_w,bar_h = 150,8; x,y = self.W-bar_w-20, self.H-bar_h-20
            pygame.draw.rect(self.sc,(50,50,50),(x,y,bar_w,bar_h))
            pygame.draw.rect(self.sc,(0,200,0),(x,y,int(bar_w*volume),bar_h))

            pygame.display.flip()
            clock.tick(60)

        # dönüş
        if self.pick_name:
            return self.pick_name, True
        return (self.text.strip() or "Player"), False
