# ui/menu.py
from __future__ import annotations
import os, pygame
from pathlib import Path
from utils.save_load import list_users, delete_game

# ────────── PROJE VE ASSET YOLLARI ──────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent          # …/AI‑Football‑Game
ASSETS_DIR   = PROJECT_ROOT / "assets"                         # sabit klasör

BG_FILE     = ASSETS_DIR / "menu_bg1.png"
LOGO_FILE   = ASSETS_DIR / "logo.png"
HOVER_SND   = ASSETS_DIR / "ui_hover.wav"
CLICK_SND   = ASSETS_DIR / "ui_click.wav"

SCROLL_STEP = 50           # her tekerlek “tik”inde kaydırılacak piksel

class Menu:
    BLUE_BG   = (200,230,255)
    BTN_BG    = (255,255,255)
    BTN_HOVER = (180,200,225)
    TXT_COLOR = (0,0,0)

    # ─────────────────────────────────────────────────────────────
    def __init__(self, screen: pygame.Surface):
        self.sc        = screen
        self.W, self.H = screen.get_size()

        # fonts
        self.font     = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 64)

        # input box
        self.input_box   = pygame.Rect(self.W//2-100, self.H//2+140, 200, 40)
        self.color_inact = pygame.Color("#A9CCE3")
        self.color_act   = pygame.Color("#4B9CD3")
        self.color       = self.color_inact
        self.active, self.text = False, ""

        # state
        self.done = False
        self.cont_flag = False
        self.pick_name = None
        self.mode = "main"                 # main / new / load
        self.last_mode_switch_time = 0

        # graphics
        self.bg   = pygame.transform.scale(pygame.image.load(BG_FILE), (self.W, self.H))
        self.logo = pygame.image.load(LOGO_FILE)
        lw = self.W//4
        lh = int(self.logo.get_height() * (lw / self.logo.get_width()))
        self.logo = pygame.transform.scale(self.logo, (lw, lh))
        self.logo_alpha, self.fade_in_speed = 0, 3

        # sounds
        self.snd_hover = pygame.mixer.Sound(HOVER_SND)
        self.snd_click = pygame.mixer.Sound(CLICK_SND)
        self.snd_hover.set_volume(0.4)
        self.snd_click.set_volume(0.5)

        # saved‑game list + scroll
        self.scroll_y = 0           # dikey kaydırma ofseti
        self._refresh_users()

    # ─────────────────────────────────────────────────────────────
    def _refresh_users(self):
        self.users = list_users()
        self.scroll_y = 0           # liste değişince başa sar
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

    # tek seferlik hover sesi
    def _play_hover_once(self, key: str, is_hover: bool):
        if not hasattr(self, "_hover_state"):
            self._hover_state = {}
        if is_hover and not self._hover_state.get(key, False):
            self.snd_hover.play()
        self._hover_state[key] = is_hover

    # ─────────────────────────────────────────────────────────────
    def run(self, _: bool):
        clock  = pygame.time.Clock()
        volume = pygame.mixer.music.get_volume()

        while not self.done:
            now = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()

            # ——— Event loop ———
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); exit()

                # tekerlek olayı → scroll
                if ev.type == pygame.MOUSEWHEEL and self.mode == "load":
                    self.scroll_y += -ev.y * SCROLL_STEP        # yukarı = pozitif
                    self.scroll_y = min(0, self.scroll_y)       # en üste sınır
                    self._recompute_rects()

                # sol‑klik
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    back_rect = pygame.Rect(20,20,220,50)
                    if self.mode in ('new','load') and back_rect.collidepoint(ev.pos):
                        self.snd_click.play()
                        self.mode="main"; self.text=""; self.active=False
                        continue

                    # MAIN screen
                    if self.mode == "main":
                        btns = {
                            "new":  pygame.Rect(self.W//2-100, self.H//2+30 ,200,40),
                            "load": pygame.Rect(self.W//2-100, self.H//2+90 ,200,40),
                            "quit": pygame.Rect(self.W//2-100, self.H//2+150,200,40)
                        }
                        if   btns["new"].collidepoint(ev.pos):
                            self.snd_click.play(); self.mode="new";  self.last_mode_switch_time=now
                        elif btns["load"].collidepoint(ev.pos):
                            self.snd_click.play(); self.mode="load"; self.last_mode_switch_time=now
                            self._refresh_users()
                        elif btns["quit"].collidepoint(ev.pos):
                            self.snd_click.play(); pygame.quit(); exit()

                    # NEW screen
                    if self.mode == "new":
                        self.active = self.input_box.collidepoint(ev.pos)
                        self.color  = self.color_act if self.active else self.color_inact

                    # LOAD screen
                    if self.mode == "load" and now - self.last_mode_switch_time > 200:
                        for name, r, dr in zip(self.users, self.user_rects, self.del_rects):
                            if r.collidepoint(ev.pos):
                                self.snd_click.play()
                                self.pick_name, self.cont_flag, self.done = name, True, True
                            if dr.collidepoint(ev.pos):
                                self.snd_click.play()
                                delete_game(name)
                                self._refresh_users()
                                break   # listeler değişti, döngü kır

                # klavye
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_PLUS, pygame.K_KP_PLUS):
                        volume = min(1.0, volume+0.1); pygame.mixer.music.set_volume(volume)
                    elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        volume = max(0.0, volume-0.1); pygame.mixer.music.set_volume(volume)
                    if self.mode == "new" and self.active:
                        if   ev.key == pygame.K_RETURN: self.snd_click.play(); self.done=True
                        elif ev.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
                        else: self.text += ev.unicode

            # ——— Logo fade‑in ———
            if self.logo_alpha < 255:
                self.logo_alpha = min(255, self.logo_alpha + self.fade_in_speed)
                self.logo.set_alpha(self.logo_alpha)

            # ——— Drawing ———
            self.sc.blit(self.bg, (0,0))
            lx = (self.W - self.logo.get_width())//2
            self.sc.blit(self.logo, (lx,50))
            title = self.big_font.render("Goalai", True, (0,255,255))
            self.sc.blit(title, title.get_rect(center=(self.W//2, self.H-80)))

            # MAIN buttons
            if self.mode == "main":
                btns = {"new":(self.H//2+30,  "Start New Game"),
                        "load":(self.H//2+90, "Load Game"),
                        "quit":(self.H//2+150,"Quit")}
                for key,(y,label) in btns.items():
                    rect = pygame.Rect(self.W//2-100, y, 200,40)
                    hov  = rect.collidepoint(mouse_pos)
                    self._play_hover_once(key, hov)
                    color = self.BTN_HOVER if hov else self.BTN_BG
                    draw = rect.inflate(10,10) if hov else rect
                    pygame.draw.rect(self.sc, color, draw, border_radius=6)
                    txt = self.font.render(label, True, self.TXT_COLOR)
                    self.sc.blit(txt, (draw.x + (draw.w-txt.get_width())//2,
                                       draw.y + (draw.h-txt.get_height())//2))

            # LOAD list
            elif self.mode == "load":
                head = self.font.render("Select a saved game", True,(0,255,255))
                self.sc.blit(head, head.get_rect(center=(self.W//2, self.H//2+10)))
                for name, r, dr in zip(self.users, self.user_rects, self.del_rects):
                    hov = r.collidepoint(mouse_pos); self._play_hover_once(name, hov)
                    color = self.BTN_HOVER if hov else self.BTN_BG
                    draw  = r.inflate(10,10) if hov else r
                    pygame.draw.rect(self.sc, color, draw, border_radius=6)
                    txt = self.font.render(name, True, self.TXT_COLOR)
                    self.sc.blit(txt, (draw.x+(draw.w-txt.get_width())//2,
                                       draw.y+(draw.h-txt.get_height())//2))
                    # delete btn
                    d_hov = dr.collidepoint(mouse_pos); self._play_hover_once(f"{name}_del", d_hov)
                    d_col = self.BTN_HOVER if d_hov else (255,80,80)
                    d_draw= dr.inflate(6,6) if d_hov else dr
                    pygame.draw.rect(self.sc, d_col, d_draw, border_radius=4)
                    x_surf= self.font.render("x", True, (255,255,255))
                    self.sc.blit(x_surf, (d_draw.x+(d_draw.w-x_surf.get_width())//2,
                                          d_draw.y+(d_draw.h-x_surf.get_height())//2))

            # NEW screen
            elif self.mode == "new":
                txt = self.font.render(self.text, True, self.TXT_COLOR)
                self.input_box.w = max(200, txt.get_width()+10)
                self.sc.blit(txt, (self.input_box.x+5, self.input_box.y+5))
                pygame.draw.rect(self.sc, self.color, self.input_box, 2, border_radius=4)
                self._play_hover_once("input", self.input_box.collidepoint(mouse_pos))

            # Back button
            if self.mode in ("new","load"):
                br = pygame.Rect(20,20,220,50)
                hov = br.collidepoint(mouse_pos); self._play_hover_once("back", hov)
                color = self.BTN_HOVER if hov else self.BTN_BG
                draw = br.inflate(10,10) if hov else br
                pygame.draw.rect(self.sc, color, draw, border_radius=6)
                txt = self.font.render("Back to Menu", True, self.TXT_COLOR)
                self.sc.blit(txt, (draw.x+(draw.w-txt.get_width())//2,
                                   draw.y+(draw.h-txt.get_height())//2))

            # volume slider
            bar_w, bar_h = 150,8; x,y = self.W-bar_w-20, self.H-bar_h-20
            pygame.draw.rect(self.sc,(50,50,50),(x,y,bar_w,bar_h))
            pygame.draw.rect(self.sc,(0,200,0),(x,y,int(bar_w*volume),bar_h))

            pygame.display.flip()
            clock.tick(60)

        # dönüş
        if self.pick_name:
            return self.pick_name, True
        return (self.text.strip() or "Player"), False