import pygame
import os
from utils.save_load import list_users, delete_game

class Menu:
    BLUE_BG   = (200, 230, 255)
    BTN_BG    = (255, 255, 255)
    TXT_COLOR = (0, 0, 0)

    def __init__(self, screen):
        self.sc        = screen
        self.W, self.H = screen.get_size()

        # Fonts
        self.font     = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 64)

        # Text input
        self.input_box   = pygame.Rect(self.W//2 - 100, self.H//2 + 140, 200, 40)
        self.color_inact = pygame.Color('#A9CCE3')
        self.color_act   = pygame.Color('#4B9CD3')
        self.color       = self.color_inact
        self.active      = False
        self.text        = ""

        # State flags
        self.done        = False
        self.cont_flag   = False
        self.pick_name   = None
        self.mode        = "main"  # main / new / load
        self.last_mode_switch_time = 0  # for click debounce

        # Graphics
        self.bg   = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "menu_bg1.png")),
            (self.W, self.H)
        )
        self.logo = pygame.image.load(os.path.join("assets", "logo.png"))
        logo_w = self.W // 4
        logo_h = int(self.logo.get_height() * (logo_w / self.logo.get_width()))
        self.logo = pygame.transform.scale(self.logo, (logo_w, logo_h))
        self.logo_alpha   = 0
        self.fade_in_speed = 3  # alpha per frame

        # Saved‑game list
        self._refresh_users()

    # --------------------------------------------------------------------- #
    def _refresh_users(self):
        self.users = list_users()
        base_y = self.H // 2 + 40
        self.user_rects = [pygame.Rect(self.W//2 - 100, base_y + i*50, 200, 40)
                           for i in range(len(self.users))]
        self.del_rects  = [pygame.Rect(self.W//2 + 110, base_y + i*50 + 10, 20, 20)
                           for i in range(len(self.users))]

    # --------------------------------------------------------------------- #
    def run(self, has_saves: bool):
        clock  = pygame.time.Clock()
        volume = pygame.mixer.music.get_volume()

        while not self.done:
            now = pygame.time.get_ticks()

            # -------- Event handling ------------------------------------- #
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); exit()

                # --- Mouse clicks --------------------------------------- #
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    # --- GLOBAL back button (only in new/load) --------- #
                    back_rect = pygame.Rect(20, 20, 220, 50)
                    if self.mode in ('new', 'load') and back_rect.collidepoint(ev.pos):
                        self.mode = 'main'
                        self.text = ""
                        self.active = False
                        continue

                    # --- MAIN MENU buttons ------------------------------ #
                    if self.mode == 'main':
                        if self.W//2 - 100 <= ev.pos[0] <= self.W//2 + 100:
                            if self.H//2 + 30  <= ev.pos[1] <= self.H//2 + 70:
                                self.mode = 'new';  self.last_mode_switch_time = now
                            elif self.H//2 + 90 <= ev.pos[1] <= self.H//2 + 130:
                                self.mode = 'load'; self.last_mode_switch_time = now
                            elif self.H//2 + 150<= ev.pos[1] <= self.H//2 + 190:
                                pygame.quit(); exit()

                    # --- NEW GAME screen ------------------------------- #
                    if self.mode == 'new':
                        self.active = self.input_box.collidepoint(ev.pos)
                        self.color  = self.color_act if self.active else self.color_inact

                    # --- LOAD GAME screen ------------------------------ #
                    if self.mode == 'load' and now - self.last_mode_switch_time > 200:
                        for name, rect, drect in zip(self.users, self.user_rects, self.del_rects):
                            if rect.collidepoint(ev.pos):
                                self.pick_name = name
                                self.cont_flag = True
                                self.done = True
                            if drect.collidepoint(ev.pos):
                                delete_game(name)
                                self._refresh_users()

                # --- Keyboard input ------------------------------------ #
                if ev.type == pygame.KEYDOWN:
                    # volume control always active
                    if ev.key in (pygame.K_PLUS, pygame.K_KP_PLUS):
                        volume = min(1.0, volume + 0.1)
                        pygame.mixer.music.set_volume(volume)
                    elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        volume = max(0.0, volume - 0.1)
                        pygame.mixer.music.set_volume(volume)

                    # text typing (only in NEW)
                    if self.mode == 'new' and self.active:
                        if ev.key == pygame.K_RETURN:
                            self.done = True
                        elif ev.key == pygame.K_BACKSPACE:
                            self.text = self.text[:-1]
                        else:
                            self.text += ev.unicode

            # -------- Logo fade‑in -------------------------------------- #
            if self.logo_alpha < 255:
                self.logo_alpha = min(255, self.logo_alpha + self.fade_in_speed)
                self.logo.set_alpha(self.logo_alpha)

            # -------- Drawing ------------------------------------------- #
            self.sc.blit(self.bg, (0, 0))

            # logo
            logo_x = (self.W - self.logo.get_width()) // 2
            self.sc.blit(self.logo, (logo_x, 50))

            # title fixed at bottom
            title = self.big_font.render("Goalai Football Game", True, (0,255,255))
            self.sc.blit(title, title.get_rect(center=(self.W//2, self.H - 80)))

            # --- main menu buttons ----
            if self.mode == 'main':
                btn_new  = pygame.Rect(self.W//2 - 100, self.H//2 + 30 , 200, 40)
                btn_load = pygame.Rect(self.W//2 - 100, self.H//2 + 90 , 200, 40)
                btn_quit = pygame.Rect(self.W//2 - 100, self.H//2 + 150, 200, 40)
                for btn in (btn_new, btn_load, btn_quit):
                    pygame.draw.rect(self.sc, self.BTN_BG, btn)
                self.sc.blit(self.font.render("Start New Game", True, self.TXT_COLOR), (btn_new.x+10 , btn_new.y+8))
                self.sc.blit(self.font.render("Load Game",       True, self.TXT_COLOR), (btn_load.x+10, btn_load.y+8))
                self.sc.blit(self.font.render("Quit",            True, self.TXT_COLOR), (btn_quit.x+10, btn_quit.y+8))

            # --- load game screen ----
            elif self.mode == 'load':
                head = self.font.render("Select a saved game", True, (0,255,255))
                self.sc.blit(head, head.get_rect(center=(self.W//2, self.H//2 + 10)))
                for name, r, dr in zip(self.users, self.user_rects, self.del_rects):
                    pygame.draw.rect(self.sc, self.BTN_BG, r)
                    self.sc.blit(self.font.render(name, True, self.TXT_COLOR), (r.x+10, r.y+8))
                    pygame.draw.rect(self.sc, (255,80,80), dr)
                    self.sc.blit(self.font.render("x", True, (255,255,255)), (dr.x+4, dr.y-2))

            # --- new game screen ----
            elif self.mode == 'new':
                txtsurf = self.font.render(self.text, True, self.TXT_COLOR)
                self.input_box.w = max(200, txtsurf.get_width()+10)
                self.sc.blit(txtsurf, (self.input_box.x+5, self.input_box.y+5))
                pygame.draw.rect(self.sc, self.color, self.input_box, 2)

            # back button for load/new
            if self.mode in ('new', 'load'):
                back_btn = pygame.Rect(20, 20, 220, 50)
                pygame.draw.rect(self.sc, self.BTN_BG, back_btn)
                self.sc.blit(self.font.render("← Back to Menu", True, self.TXT_COLOR), (back_btn.x+10, back_btn.y+10))

            # --- volume slider (bottom‑right) ----
            bar_w, bar_h = 150, 8
            x = self.W - bar_w - 20
            y = self.H - bar_h - 20
            pygame.draw.rect(self.sc, (50,50,50), (x, y, bar_w, bar_h))
            pygame.draw.rect(self.sc, (0,200,0), (x, y, bar_w * volume, bar_h))

            pygame.display.flip()
            clock.tick(60)

        # -------- Return logic ----------------------------------------- #
        if self.pick_name:
            return self.pick_name, True
        name = (self.text.strip() or "Player")
        return name, False
