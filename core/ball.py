# C:\Users\yigit\OneDrive\Desktop\aigame\AI-Football-Game\core\ball.py

import os
import pygame

# Dosya yolunu belirle
_BASE_DIR    = os.path.dirname(__file__)                    # ...\AI-Football-Game\core
_PROJECT_DIR = os.path.dirname(_BASE_DIR)                  # ...\AI-Football-Game
ROOT_DIR     = os.path.dirname(_PROJECT_DIR)               # ...\aigame
_ASSET_DIR   = os.path.join(ROOT_DIR, "assets")            # ...\aigame\assets
BALL_FILE    = os.path.join(_ASSET_DIR, "ball.png")

class Ball:
    # Sadece bir kez yüklensin diye class-level cache
    _sprite = None

    def __init__(self, x, y, radius=6):
        """
        x, y   : Başlangıç pozisyonu
        radius : top yarıçapı (çizim ve çarpışma için)
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.vel_x = 0
        self.vel_y = 0
        self.max_speed = 5
        self.friction = 0.97

        # Sprite'ı yükle + ölçekle (radius*2 = çap)
        if Ball._sprite is None:
            img = pygame.image.load(BALL_FILE).convert_alpha()
            size = (radius * 3, radius * 3)
            Ball._sprite = pygame.transform.scale(img, size)
        self.sprite = Ball._sprite

    def move(self):
        # Mevcut hareket, sürtünme ve duvar sekme mantığı
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_x *= self.friction
        self.vel_y *= self.friction

        if abs(self.vel_x) < 0.05:
            self.vel_x = 0
        if abs(self.vel_y) < 0.05:
            self.vel_y = 0

        # Üst/alt duvar
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vel_y *= -1
        elif self.y + self.radius >= 600:
            self.y = 600 - self.radius
            self.vel_y *= -1

        # Sol/sağ kenar (kaleye girdiğinde engel yok)
        goal_top = 240
        goal_bottom = 360

        if self.x - self.radius < 0:
            if not (goal_top <= self.y <= goal_bottom):
                self.x = self.radius
                self.vel_x *= -1
        elif self.x + self.radius > 800:
            if not (goal_top <= self.y <= goal_bottom):
                self.x = 800 - self.radius
                self.vel_x *= -1

    def kick(self, power_x, power_y):
        self.vel_x += power_x
        self.vel_y += power_y
        speed = (self.vel_x**2 + self.vel_y**2)**0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.vel_x *= scale
            self.vel_y *= scale

    def draw(self, screen):
        """Top sprite’ını merkez konumuna göre blit’ler."""
        # Sprite’ın üst-sol köşe koordinatını hesapla
        blit_x = int(self.x - self.radius)
        blit_y = int(self.y - self.radius)
        screen.blit(self.sprite, (blit_x, blit_y))
