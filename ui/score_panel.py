# ui/score_panel.py
import pygame, random

class ScorePanel:
    """Skor çubuğu titreme + fade animasyonu (gol sonrası)."""

    H = 40          # panel yüksekliği
    SHAKE_FRAMES = 15
    FADE_FRAMES  = 45

    def __init__(self, width: int, font: pygame.font.Font):
        self.W = width
        self.font = font
        self.t = -1          # animasyon sayacı (negatif = oynama yok)
        self.last_scores = (0, 0)

    # ----------------------------------------------
    def trigger(self, score_red: int, score_blue: int):
        """Gol sonrası animasyonu başlat."""
        self.t = 0
        self.last_scores = (score_red, score_blue)

    # ----------------------------------------------
    def draw(self, surf: pygame.Surface,
             score_red: int, score_blue: int,
             clk: pygame.time.Clock):
        """
        Her kare çağır.  Animasyon varsa titrer & fade‑out yapar,
        yoksa düz panel çizer.
        """
        # —— arka plan (hafif transparan koyu) ——
        bar = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        bar.fill((30, 30, 30, 220))            # (r,g,b,alpha)
        surf.blit(bar, (0, 0))

        # —— kutu yardımcı ——
        def box(x, color):
            rect = pygame.Rect(x, 5, 110, 30)
            pygame.draw.rect(surf, color, rect, border_radius=6)
            return rect

        # —— animasyon parametreleri ——
        shake = 0
        alpha = 255
        if 0 <= self.t < self.SHAKE_FRAMES + self.FADE_FRAMES:
            if self.t < self.SHAKE_FRAMES:                 # titreme
                shake = 3
            else:                                          # fade‑out
                k = (self.t - self.SHAKE_FRAMES) / self.FADE_FRAMES
                alpha = int(255 * (1 - k))
            self.t += 1                                    # ilerlet

        # —— kutular + skor metinleri ——
        red_rect  = box(10,       (200, 0, 0))
        blue_rect = box(self.W-120, (0, 0, 200))

        for rect in (red_rect, blue_rect):
            rect.move_ip(random.randint(-shake, shake),
                         random.randint(-shake, shake))

        txt_red  = self.font.render(str(score_red),  True, (255,255,255))
        txt_blue = self.font.render(str(score_blue), True, (255,255,255))
        txt_red.set_alpha(alpha); txt_blue.set_alpha(alpha)

        surf.blit(txt_red,  txt_red .get_rect(center=red_rect.center))
        surf.blit(txt_blue, txt_blue.get_rect(center=blue_rect.center))